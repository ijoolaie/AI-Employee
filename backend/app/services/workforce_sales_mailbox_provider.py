"""Operator-controlled mailbox adapter for real Sales Employee replies.

This provider is deliberately polling-based and narrow. It reads only messages
that reference a Message-ID previously emitted by this application's governed
SMTP worker. It never accepts tenant/provider selection from message content,
and it never treats an arbitrary mailbox message as a sales response.
"""
from __future__ import annotations

import email
import imaplib
import re
import ssl
import uuid
from dataclasses import dataclass
from email.header import decode_header, make_header

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.audit_log import AuditLog


@dataclass(frozen=True)
class MailboxResponse:
    tenant_id: uuid.UUID
    provider_message_id: str
    event_id: str
    response_text: str
    sender: str
    subject: str


_MESSAGE_ID_RE = re.compile(r"<([^>]+)>")
_MAX_MESSAGES_PER_POLL = 25


def _header_text(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _message_ids(value: str | None) -> set[str]:
    if not value:
        return set()
    return {match.group(1).strip() for match in _MESSAGE_ID_RE.finditer(value)}


def _response_text(message: email.message.Message) -> str:
    parts: list[str] = []
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_disposition() == "attachment":
                continue
            if part.get_content_type() != "text/plain":
                continue
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            parts.append(payload.decode(charset, errors="replace"))
    else:
        payload = message.get_payload(decode=True)
        if payload is not None:
            charset = message.get_content_charset() or "utf-8"
            parts.append(payload.decode(charset, errors="replace"))
    text = "\n".join(parts).strip()
    return text[:8000]


def _connect(settings):
    if not settings.sales_inbound_mailbox_host:
        raise RuntimeError("Sales inbound mailbox host is not configured")
    if not settings.sales_inbound_mailbox_username:
        raise RuntimeError("Sales inbound mailbox username is not configured")
    if not settings.sales_inbound_mailbox_password:
        raise RuntimeError("Sales inbound mailbox password is not configured")

    context = ssl.create_default_context()
    client = imaplib.IMAP4_SSL(
        settings.sales_inbound_mailbox_host,
        settings.sales_inbound_mailbox_port,
        ssl_context=context,
        timeout=settings.sales_inbound_mailbox_timeout_seconds,
    )
    client.login(
        settings.sales_inbound_mailbox_username,
        settings.sales_inbound_mailbox_password,
    )
    return client


async def poll_sales_replies(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID | None = None,
) -> list[MailboxResponse]:
    """Find real mailbox replies that correlate to immutable delivery events.

    The query is intentionally limited to recent delivered events and the IMAP
    search is limited to each known application Message-ID. No arbitrary
    mailbox message is accepted.

    Search diagnostics are deliberately metadata-only: counts and statuses are
    logged, never message bodies, sender addresses, credentials, or secrets.
    """
    settings = get_settings()
    provider = (settings.sales_inbound_provider_name or "none").strip().lower()
    if provider != "imap-mailbox":
        raise RuntimeError("Sales inbound mailbox provider is not configured")

    stmt = (
        select(AuditLog)
        .where(
            AuditLog.action == "sales.engagement",
            AuditLog.resource_type == "sales_engagement",
            AuditLog.metadata_.op("->>")("event_type") == "outreach_delivered",
        )
        .order_by(AuditLog.created_at.desc())
        .limit(_MAX_MESSAGES_PER_POLL)
    )
    if tenant_id is not None:
        stmt = stmt.where(AuditLog.tenant_id == tenant_id)

    rows = list((await db.execute(stmt)).scalars().all())
    candidates: list[tuple[uuid.UUID, str]] = []
    for row in rows:
        provider_message_id = (row.metadata_ or {}).get("provider_message_id")
        if provider_message_id:
            candidates.append((row.tenant_id, str(provider_message_id)))

    if not candidates:
        print("W10 IMAP MAILBOX DIAGNOSTIC candidates=0")
        return []

    print(f"W10 IMAP MAILBOX DIAGNOSTIC candidates={len(candidates)}")

    mailbox = _connect(settings)
    try:
        select_status, select_data = mailbox.select(
            settings.sales_inbound_mailbox_folder, readonly=True
        )
        message_count = 0
        if select_data and select_data[0]:
            try:
                message_count = int(select_data[0])
            except (TypeError, ValueError):
                message_count = 0
        print(
            "W10 IMAP MAILBOX SELECT "
            f"folder={settings.sales_inbound_mailbox_folder} "
            f"status={select_status} messages={message_count}"
        )
        if select_status != "OK":
            raise RuntimeError("Sales inbound mailbox folder selection failed")

        results: list[MailboxResponse] = []
        seen_uids: set[str] = set()

        for candidate_index, (candidate_tenant, provider_message_id) in enumerate(
            candidates, start=1
        ):
            # The SMTP worker emits <outbox-{uuid}@ai-employee.local>. Some
            # providers normalize header search terms, so try the full token
            # and the bare application Message-ID token. Acceptance below
            # remains strict: the fetched RFC822 headers must contain the exact
            # provider_message_id.
            token = f"<{provider_message_id}@ai-employee.local>"
            search_values = (token, provider_message_id)
            candidate_matches = 0
            candidate_valid = 0

            for header in ("In-Reply-To", "References"):
                for search_value in search_values:
                    status, data = mailbox.uid(
                        "SEARCH", None, "HEADER", header, search_value
                    )
                    raw_uids = (data[0] or b"") if status == "OK" and data else b""
                    uids = raw_uids.split()
                    candidate_matches += len(uids)
                    print(
                        "W10 IMAP MAILBOX SEARCH "
                        f"candidate={candidate_index}/{len(candidates)} "
                        f"header={header} term={'full' if search_value == token else 'bare'} "
                        f"status={status} matches={len(uids)}"
                    )
                    await _process_uids(
                        mailbox,
                        uids,
                        seen_uids,
                        candidate_index,
                        len(candidates),
                        candidate_tenant,
                        provider_message_id,
                        results,
                    )
                    candidate_valid = sum(
                        1 for item in results if item.provider_message_id == provider_message_id
                    )

            # Fallback diagnostic path: some IMAP implementations search
            # headers differently or expose reply headers only through a
            # full-message TEXT search. This path is discovery-only; the
            # fetched message must still pass the exact header correlation
            # check above before acceptance.
            for search_value in search_values:
                status, data = mailbox.uid("SEARCH", None, "TEXT", search_value)
                raw_uids = (data[0] or b"") if status == "OK" and data else b""
                uids = raw_uids.split()
                candidate_matches += len(uids)
                print(
                    "W10 IMAP MAILBOX SEARCH "
                    f"candidate={candidate_index}/{len(candidates)} "
                    f"header=TEXT term={'full' if search_value == token else 'bare'} "
                    f"status={status} matches={len(uids)}"
                )
                await _process_uids(
                    mailbox,
                    uids,
                    seen_uids,
                    candidate_index,
                    len(candidates),
                    candidate_tenant,
                    provider_message_id,
                    results,
                )
                candidate_valid = sum(
                    1 for item in results if item.provider_message_id == provider_message_id
                )

            print(
                "W10 IMAP MAILBOX CANDIDATE RESULT "
                f"candidate={candidate_index}/{len(candidates)} "
                f"search_matches={candidate_matches} valid_responses={candidate_valid}"
            )
        return results
    finally:
        try:
            mailbox.close()
        except Exception:
            pass
        try:
            mailbox.logout()
        except Exception:
            pass


async def _process_uids(
    mailbox,
    uids: list[bytes],
    seen_uids: set[str],
    candidate_index: int,
    candidate_count: int,
    candidate_tenant: uuid.UUID,
    provider_message_id: str,
    results: list[MailboxResponse],
) -> None:
    for raw_uid in uids:
        uid = raw_uid.decode("ascii", errors="ignore")
        if not uid or uid in seen_uids:
            continue
        seen_uids.add(uid)
        fetch_status, fetched = mailbox.uid("FETCH", uid, "(RFC822)")
        if fetch_status != "OK":
            print(
                "W10 IMAP MAILBOX FETCH "
                f"candidate={candidate_index}/{candidate_count} status={fetch_status}"
            )
            continue
        raw_message = next(
            (
                item[1]
                for item in fetched
                if isinstance(item, tuple) and len(item) > 1
            ),
            None,
        )
        if not raw_message:
            continue
        message = email.message_from_bytes(raw_message)
        referenced = (
            _message_ids(message.get("In-Reply-To"))
            | _message_ids(message.get("References"))
        )
        if provider_message_id not in referenced:
            print(
                "W10 IMAP MAILBOX CORRELATION REJECT "
                f"candidate={candidate_index}/{candidate_count} reason=header_mismatch"
            )
            continue
        message_id = next(iter(_message_ids(message.get("Message-ID"))), "")
        if not message_id:
            print(
                "W10 IMAP MAILBOX CORRELATION REJECT "
                f"candidate={candidate_index}/{candidate_count} reason=missing_message_id"
            )
            continue
        response_text = _response_text(message)
        if not response_text:
            print(
                "W10 IMAP MAILBOX CORRELATION REJECT "
                f"candidate={candidate_index}/{candidate_count} reason=empty_text"
            )
            continue
        results.append(
            MailboxResponse(
                tenant_id=candidate_tenant,
                provider_message_id=provider_message_id,
                event_id=f"message:{message_id}",
                response_text=response_text,
                sender=_header_text(message.get("From")),
                subject=_header_text(message.get("Subject")),
            )
        )
