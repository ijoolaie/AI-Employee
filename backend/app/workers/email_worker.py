"""SMTP worker consuming durable email outbox messages."""
from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from uuid import UUID

from app.core.config import get_settings
from app.core.database import worker_db_session
from app.core.exceptions import ValidationAppError
from app.models.outbox import OutboxMessage
from app.services.agent_policy_engine import PolicyRequest, assert_authorized
from app.workers.celery_app import celery_app


async def _authorize_deferred_agent_side_effect(db, row: OutboxMessage) -> None:
    """Revalidate current Agent authority immediately before SMTP execution."""
    proof = (row.payload or {}).get("_agent_governance")
    if proof is None:
        return
    if not isinstance(proof, dict):
        raise ValidationAppError("Malformed Agent outbox governance binding")
    try:
        tenant_id = UUID(str(proof["tenant_id"]))
        agent_instance_id = UUID(str(proof["agent_instance_id"]))
        run_id = UUID(str(proof["run_id"]))
        tool_name = str(proof["tool_name"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationAppError("Malformed Agent outbox governance binding") from exc
    if tenant_id != row.tenant_id or not tool_name:
        raise ValidationAppError("Agent outbox governance binding mismatch")

    await assert_authorized(
        db,
        PolicyRequest(
            tenant_id=tenant_id,
            agent_instance_id=agent_instance_id,
            action="tool.execute",
            tool_name=tool_name,
            required_permission="run.execute",
            run_id=run_id,
        ),
    )


def _build_email(payload: dict, outbox_id: str, settings) -> EmailMessage:
    """Build an email with a stable Message-ID for this durable outbox item."""
    msg = EmailMessage()
    msg["Message-ID"] = f"<outbox-{outbox_id}@ai-employee.local>"
    msg["From"] = settings.smtp_from_email
    msg["To"] = ", ".join(payload["to"])
    msg["Subject"] = payload["subject"]
    msg.set_content(payload["body"])
    return msg


async def _send(outbox_id: str) -> None:
    async with worker_db_session() as db:
        row = await db.get(OutboxMessage, outbox_id)
        if row is None or row.status in {"dispatched", "dead", "uncertain"}:
            return
        if row.status not in {"processing", "pending"}:
            return
        settings = get_settings()
        payload = row.payload
        try:
            await _authorize_deferred_agent_side_effect(db, row)

            # Once SMTP is attempted, the external outcome cannot be made
            # atomic with the DB commit. Persist an explicit uncertain state
            # first. A worker crash after SMTP acceptance therefore cannot be
            # mistaken for a safe-to-retry failure.
            row.status = "uncertain"
            await db.commit()

            msg = _build_email(payload, str(row.id), settings)
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_use_starttls:
                    smtp.starttls()
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password or "")
                smtp.send_message(msg)

            from app.services.outbox_service import mark_dispatched
            await mark_dispatched(db, row)
        except Exception as exc:
            from app.services.outbox_service import mark_retry
            await mark_retry(db, row, str(exc), delay_seconds=min(300, 10 * max(1, row.attempts)))
        await db.commit()


@celery_app.task(name="email.send")
def send_email_task(outbox_id: str) -> None:
    asyncio.run(_send(outbox_id))
