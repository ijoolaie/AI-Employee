"""Audit Log write path.

Kept deliberately dependency-light (no import of other services) so that
any layer — API routes, services, Celery workers, the AI Gateway — can
record an audit entry without risking circular imports.

Per docs v1.2 §3.4: called for every sensitive operation. Failures to
write an audit entry must never abort the primary operation (an audit
log is a side channel), so callers should wrap `record()` calls that
happen after the main commit, or accept a best-effort write within the
same transaction for operations where the two must be atomic.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def record(
    db: AsyncSession,
    *,
    action: str,
    actor_type: str = "user",
    actor_id: UUID | str | None = None,
    tenant_id: UUID | str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    status: str = "success",
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Insert one audit entry. Does not commit — caller controls the transaction
    boundary (usually the enclosing request's session, which commits in
    app.core.database.get_db)."""
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        status=status,
        request_id=request_id,
        metadata_=metadata or {},
    )
    db.add(entry)
    await db.flush()
    return entry


async def list_logs(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    limit: int = 100,
    action: str | None = None,
    status: str | None = None,
) -> list[AuditLog]:
    """Return tenant-scoped audit entries for operational/developer inspection."""
    from sqlalchemy import select

    stmt = (
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(min(max(limit, 1), 200))
    )
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if status:
        stmt = stmt.where(AuditLog.status == status)
    result = await db.execute(stmt)
    return list(result.scalars().all())
