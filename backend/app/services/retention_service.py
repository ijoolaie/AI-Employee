"""Tenant-safe data retention and lifecycle enforcement.

This service provides a deterministic, idempotent cleanup pass for records
whose retention window has elapsed. It is deliberately explicit about the
record classes it owns so operational jobs cannot accidentally delete
unrelated tenant data.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer_conversation_slot import CustomerConversationSlot

from app.models.file import FileObject
from app.models.memory import EmployeeMemory
from app.models.usage import UsageEvent

DEFAULT_RETENTION_DAYS = 365
CUSTOMER_SLOT_PURGE_BATCH_SIZE = 500


async def enforce_retention(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    now: datetime | None = None,
) -> dict[str, int | str]:
    """Delete expired operational records for exactly one tenant.

    Files are soft-deleted when stale; immutable audit logs are never deleted
    by retention. Usage events remain subject to the configured retention
    window. Memory entries honor an explicit
    ``expires_at`` lifecycle first, while the retention window remains a
    safety ceiling for terminal lifecycle states.
    """
    if retention_days < 1 or retention_days > 3650:
        raise ValueError("retention_days must be between 1 and 3650")

    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    counts: dict[str, int | str] = {"tenant_id": str(tenant_id), "cutoff": cutoff.isoformat()}

    usage_result = await db.execute(
        delete(UsageEvent).where(
            UsageEvent.tenant_id == tenant_id,
            UsageEvent.created_at < cutoff,
        )
    )
    counts["usage_events_deleted"] = usage_result.rowcount or 0

    memory_result = await db.execute(
        delete(EmployeeMemory).where(
            EmployeeMemory.tenant_id == tenant_id,
            or_(
                EmployeeMemory.expires_at <= now,
                and_(
                    EmployeeMemory.created_at < cutoff,
                    EmployeeMemory.status.in_(["expired", "deleted", "superseded"]),
                ),
            ),
        )
    )
    counts["memory_rows_deleted"] = memory_result.rowcount or 0

    stale_files = await db.execute(
        select(FileObject).where(
            FileObject.tenant_id == tenant_id,
            FileObject.created_at < cutoff,
            FileObject.status == "active",
        )
    )
    file_rows = list(stale_files.scalars().all())
    for row in file_rows:
        row.status = "deleted"
        row.deleted_at = now
    counts["files_soft_deleted"] = len(file_rows)

    # Slot values are short-lived customer-provided data. Their individual TTL
    # is authoritative: purge at expiry without applying the general 365-day
    # retention window. A bounded SKIP LOCKED batch makes concurrent workers
    # safe; repeated retention runs drain any backlog. Only slot rows are
    # deleted, never their source messages or conversations.
    expired_slots = (
        select(CustomerConversationSlot.id)
        .where(
            CustomerConversationSlot.tenant_id == tenant_id,
            CustomerConversationSlot.expires_at <= now,
        )
        .order_by(CustomerConversationSlot.expires_at, CustomerConversationSlot.id)
        .limit(CUSTOMER_SLOT_PURGE_BATCH_SIZE)
        .with_for_update(skip_locked=True)
        .cte("expired_customer_slots")
    )
    slots_result = await db.execute(
        delete(CustomerConversationSlot)
        .where(CustomerConversationSlot.id.in_(select(expired_slots.c.id)))
        .returning(CustomerConversationSlot.id)
    )
    counts["customer_slots_deleted"] = len(slots_result.scalars().all())

    await db.flush()
    counts["enforced_at"] = now.isoformat()
    return counts
