"""SMTP worker consuming durable email outbox messages."""
from __future__ import annotations
import asyncio
import smtplib
from email.message import EmailMessage
from app.core.config import get_settings
from app.core.database import worker_db_session
from app.models.outbox import OutboxMessage
from app.workers.celery_app import celery_app

async def _send(outbox_id: str) -> None:
    async with worker_db_session() as db:
        row = await db.get(OutboxMessage, outbox_id)
        if row is None or row.status not in {"processing", "pending"}:
            return
        settings = get_settings()
        payload = row.payload
        msg = EmailMessage()
        msg["From"] = settings.smtp_from_email
        msg["To"] = ", ".join(payload["to"])
        msg["Subject"] = payload["subject"]
        msg.set_content(payload["body"])
        try:
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
