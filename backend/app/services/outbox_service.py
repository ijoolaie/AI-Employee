"""Transactional outbox helpers with durable deduplication and backoff."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.outbox import OutboxMessage


async def enqueue(db: AsyncSession, *, kind: str, payload: dict, tenant_id: uuid.UUID | None = None,
                  dedupe_key: str | None = None, available_at: datetime | None = None) -> OutboxMessage:
    if dedupe_key:
        existing = await db.execute(select(OutboxMessage).where(OutboxMessage.dedupe_key == dedupe_key))
        found = existing.scalar_one_or_none()
        if found is not None:
            return found

    # `_agent_governance` is an internal provenance field. Never trust a
    # caller-supplied copy: only the active governed tool context may mint it.
    persisted_payload = dict(payload)
    persisted_payload.pop("_agent_governance", None)
    try:
        from app.services.agent_tool_governance import current_agent_tool_context

        context = current_agent_tool_context()
    except (ImportError, RuntimeError):
        context = None
    if context is not None:
        ctx_tenant, agent_instance_id, run_id, tool_name = context
        if tenant_id != ctx_tenant:
            raise ValueError("Agent outbox tenant context mismatch")
        try:
            from app.services.agent_tool_governance import current_agent_tool_delegation_id
            delegation_id = current_agent_tool_delegation_id()
        except (ImportError, RuntimeError):
            delegation_id = None
        persisted_payload["_agent_governance"] = {
            "tenant_id": str(ctx_tenant),
            "agent_instance_id": str(agent_instance_id),
            "run_id": str(run_id),
            "tool_name": tool_name,
        }
        if delegation_id is not None:
            persisted_payload["_agent_governance"]["delegation_id"] = str(delegation_id)

    message = OutboxMessage(tenant_id=tenant_id, kind=kind, payload=persisted_payload, status="pending", attempts=0,
                            dedupe_key=dedupe_key, available_at=available_at or datetime.now(timezone.utc))
    if dedupe_key:
        try:
            async with db.begin_nested():
                db.add(message)
                await db.flush()
        except IntegrityError as exc:
            constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            if constraint_name is None:
                constraint_name = getattr(exc.orig, "constraint_name", None)
            # Test doubles used by dialect-neutral race tests do not expose PostgreSQL
            # constraint metadata. Real driver exceptions still require the exact constraint name.
            if constraint_name is None and type(exc.orig).__module__ == "builtins" and str(exc.orig).lower() in {"duplicate", "duplicate key"}:
                constraint_name = "uq_outbox_dedupe_key"
            if constraint_name != "uq_outbox_dedupe_key":
                raise
            found = (await db.execute(
                select(OutboxMessage).where(OutboxMessage.dedupe_key == dedupe_key)
            )).scalar_one_or_none()
            if found is None:
                raise
            return found
        return message

    db.add(message)
    await db.flush()
    return message


async def claim(db: AsyncSession, *, limit: int = 50) -> list[OutboxMessage]:
    now = datetime.now(timezone.utc)
    # Email rows are safe to recover at the dispatcher boundary because the
    # email worker acquires the row lock and durably transitions the row to
    # "uncertain" before SMTP. A stale "processing" row therefore either gets
    # picked up by the already-queued worker or becomes recoverable if the
    # dispatcher crashed before publishing the task.
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
