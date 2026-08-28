"""Tenant-scoped WorkItem execution history derived from the canonical audit trail."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.work_item import WorkItem

router = APIRouter(prefix="/work-items", tags=["work-item-history"])


@router.get("/{work_item_id}/history")
async def history(
    work_item_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = await db.get(WorkItem, work_item_id)
    if item is None or item.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="work item not found")

    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.tenant_id == current_user.tenant_id,
            AuditLog.resource_type == "work_item",
            AuditLog.resource_id == str(work_item_id),
        )
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
    )
    events = result.scalars().all()
    return {
        "work_item_id": work_item_id,
        "status": item.status.value,
        "executor_type": item.executor_type.value if item.executor_type else None,
        "executor_id": item.executor_id,
        "events": [
            {
                "id": event.id,
                "action": event.action,
                "actor_type": event.actor_type,
                "actor_id": event.actor_id,
                "status": event.status,
                "request_id": event.request_id,
                "metadata": event.metadata_,
                "created_at": event.created_at,
            }
            for event in events
        ],
    }
