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

    persisted_payload = dict(payload)
    try:
        from app.services.agent_tool_governance import current_agent_tool_context

        context = current_agent_tool_context()
    except (ImportError, RuntimeError):
        context = None
    if context is not None:
        ctx_tenant, agent_instance_id, run_id, tool_name = context
        if tenant_id != ctx_tenant:
            raise ValueError("Agent outbox tenant context mismatch")
        persisted_payload["_agent_governance"] = {
            "tenant_id": str(ctx_tenant),
            "agent_instance_id": str(agent_instance_id),
            "run_id": str(run_id),
            "tool_name": tool_name,
        }

    message = OutboxMessage(tenant_id=tenant_id, kind=kind, payload=persisted_payload, status="pending", attempts=0,
                            dedupe_key=dedupe_key, available_at=available_at or datetime.now(timezone.utc))
    db.add(message)
    await db.flush()
    return message


async def claim(db: AsyncSession, *, limit: int = 50) -> list[OutboxMessage]:
    now = datetime.now(timezone.utc)
    # A stale SMTP delivery has an unknown external outcome: the provider may
    # already have accepted the message even though the worker disappeared.
    # Never automatically reclaim email.send rows, otherwise a worker crash
    # after SMTP acceptance can produce a duplicate email. The email worker
    # durably marks the row "uncertain" before the external side effect.
    claimable = (
        (OutboxMessage.status == "pending") & (OutboxMessage.available_at <= now)
    ) | (
        (OutboxMessage.status == "processing")
        & (OutboxMessage.available_at <= now - timedelta(minutes=5))
        & (OutboxMessage.kind != "email.send")
    )
    result = await db.execute(
        select(OutboxMessage)
        .where(claimable)
        .with_for_update(skip_locked=True)
        .limit(limit)
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
