"""Audit helpers for the unified human/AI execution lifecycle."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit_service import record


async def record_execution_event(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    work_item_id: UUID,
    action: str,
    actor_type: str,
    actor_id: UUID | None = None,
    status: str = "success",
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
):
    """Write a minimal, tenant-scoped execution audit event."""
    return await record(
        db,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        tenant_id=tenant_id,
        resource_type="work_item",
        resource_id=work_item_id,
        status=status,
        request_id=request_id,
        metadata=metadata,
    )
