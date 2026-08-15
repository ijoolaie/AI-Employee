"""Transactional outbox helpers with durable deduplication and backoff."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.outbox import OutboxMessage

async def enqueue(db: AsyncSession, *, kind: str, payload: dict, tenant_id: uuid.UUID | None = None,
                  dedupe_key: str | None = None, available_at: datetime | None = None) -> OutboxMessage:
    if dedupe_key:
        existing = await db.execute(select(OutboxMessage).where(OutboxMessage.dedupe_key == dedupe_key))
        found = existing.scalar_one_or_none()
        if found is not None:
            return found
    message = OutboxMessage(tenant_id=tenant_id, kind=kind, payload=payload, status="pending", attempts=0,
                            dedupe_key=dedupe_key, available_at=available_at or datetime.now(timezone.utc))
    db.add(message)
    await db.flush()
    return message

async def claim(db: AsyncSession, *, limit: int = 50) -> list[OutboxMessage]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(OutboxMessage)
        .where(((OutboxMessage.status == "pending") & (OutboxMessage.available_at <= now)) |
               ((OutboxMessage.status == "processing") & (OutboxMessage.available_at <= now - timedelta(minutes=5))))
        .with_for_update(skip_locked=True).limit(limit)
    )
    rows = list(result.scalars().all())
    for row in rows:
        row.status = "processing"
        row.attempts += 1
    await db.flush()
    return rows

async def mark_dispatched(db: AsyncSession, message: OutboxMessage) -> None:
    message.status = "dispatched"
    message.dispatched_at = datetime.now(timezone.utc)
    message.last_error = None
    await db.flush()

async def mark_retry(db: AsyncSession, message: OutboxMessage, error: str, delay_seconds: int = 10) -> None:
    from app.core.config import get_settings
    message.last_error = error[:4000]
    if message.attempts >= get_settings().outbox_max_attempts:
        message.status = "dead"
        message.dead_at = datetime.now(timezone.utc)
        message.available_at = datetime.now(timezone.utc)
    else:
        message.status = "pending"
        message.available_at = datetime.now(timezone.utc) + timedelta(seconds=max(1, delay_seconds))
    await db.flush()

async def replay(db: AsyncSession, message: OutboxMessage) -> OutboxMessage:
    message.status = "pending"
    message.available_at = datetime.now(timezone.utc)
    message.last_error = None
    message.dead_at = None
    message.replayed_at = datetime.now(timezone.utc)
    await db.flush()
    return message
