"""Tenant-safe data retention and lifecycle enforcement.

This service provides a deterministic, idempotent cleanup pass for records
whose retention window has elapsed. It is deliberately explicit about the
record classes it owns so operational jobs cannot accidentally delete
unrelated tenant data.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.file import FileObject
from app.models.memory import EmployeeMemory
from app.models.usage import UsageEvent

DEFAULT_RETENTION_DAYS = 365


async def enforce_retention(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    now: datetime | None = None,
) -> dict[str, int | str]:
    """Delete expired operational records for exactly one tenant.

    Files are soft-deleted when stale; audit logs and usage events are hard
    deleted because they are append-only operational records subject to the
    configured retention window. Memory entries use their explicit
    ``expires_at`` lifecycle first and retention as a safety ceiling.
    """
    if retention_days < 1 or retention_days > 3650:
        raise ValueError("retention_days must be between 1 and 3650")

    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    counts: dict[str, int | str] = {"tenant_id": str(tenant_id), "cutoff": cutoff.isoformat()}

    audit_result = await db.execute(
        delete(AuditLog).where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.created_at < cutoff,
        )
    )
    counts["audit_logs_deleted"] = audit_result.rowcount or 0

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
            EmployeeMemory.created_at < cutoff,
            EmployeeMemory.status.in_(["expired", "deleted", "superseded"]),
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

    await db.flush()
    counts["enforced_at"] = now.isoformat()
    return counts
