"""Governed outbound provider for the Sales Employee.

The provider is intentionally operator-configured. The Sales Employee cannot
choose an arbitrary SMTP host or bypass the approval/tool boundary. When the
provider is not configured, execution fails closed without creating an
external side effect.
"""
from __future__ import annotations

from hashlib import sha256
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.services import outbox_service


async def execute_sales_outreach(
    *,
    db,
    tenant_id,
    arguments: dict[str, Any],
    tool_call_id: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    provider = (settings.sales_outreach_provider_name or "none").strip().lower()

    if provider != "smtp":
        return {
            "provider": provider,
            "provider_execution": "not_configured",
            "executed": False,
            "external_side_effect": False,
            "reason": "Sales outreach provider is not configured",
        }

    if db is None or tenant_id is None:
        raise ValidationAppError(
            "Configured sales outreach requires an active tenant Run context"
        )

    recipients = arguments.get("to") or []
    subject = arguments.get("subject") or ""
    body = arguments.get("message") or arguments.get("body") or ""
    if not recipients or not subject or not body:
        raise ValidationAppError(
            "Configured sales outreach requires to, subject, and message"
        )

    # The existing send_email boundary owns the SMTP allowlist and credentials.
    # Sales reuses the same transactional outbox contract rather than opening
    # another SMTP path or allowing model-controlled transport settings.
    allowed_domains = {
        d.strip().lower().lstrip("@")
        for d in settings.smtp_allowed_recipient_domains
        if d.strip()
    }
    if not settings.smtp_host or not settings.smtp_from_email or not allowed_domains:
        raise ValidationAppError(
            "Sales SMTP integration is not configured or recipient allowlist is empty; fail-closed"
        )

    for address in recipients:
        if "@" not in address:
            raise ValidationAppError("Recipient domain is not allowed")
        domain = address.rsplit("@", 1)[1].lower()
        if domain not in allowed_domains:
            raise ValidationAppError(
                "Recipient domain is not allowed",
                details={"recipient": address},
            )

    dedupe_source = tool_call_id or sha256(
        ("|".join(recipients) + "|" + subject + "|" + body).encode("utf-8")
    ).hexdigest()
    try:
        tenant_uuid = tenant_id if isinstance(tenant_id, UUID) else UUID(str(tenant_id))
    except (TypeError, ValueError) as exc:
        raise ValidationAppError("Configured sales outreach requires a valid tenant Run context") from exc

    queued = await outbox_service.enqueue(
        db,
        kind="email.send",
        tenant_id=tenant_uuid,
        dedupe_key=f"sales-outreach:{dedupe_source}",
        payload={
            "to": recipients,
            "subject": subject,
            "body": body,
            "deal_id": arguments.get("deal_id"),
            "_sales_engagement": {"tool_call_id": tool_call_id, "deal_id": arguments.get("deal_id")},
        },
    )
    return {
        "provider": "smtp",
        "provider_execution": "queued",
        "executed": True,
        "external_side_effect": True,
        "queued": True,
        "outbox_id": str(queued.id),
        "recipient_count": len(recipients),
        "subject": subject,
    }
