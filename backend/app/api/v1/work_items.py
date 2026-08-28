"""Phase 8.3 WorkItem execution API.

All operations are tenant-scoped and expose the same execution model to
Platform, Reseller and Client workspaces through role/policy enforcement.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.work_item import WorkItem
from app.services.unified_execution import ExecutionError, UnifiedExecutionService

router = APIRouter(prefix="/work-items", tags=["work-items"])


class HumanAssignmentRequest(BaseModel):
    executor_id: UUID


class ExecutionResponse(BaseModel):
    work_item_id: UUID
    status: str
    dispatched: bool
    waiting_for_approval: bool


async def _get_work_item(db: AsyncSession, work_item_id: UUID, tenant_id: UUID) -> WorkItem:
    item = await db.get(WorkItem, work_item_id)
    if item is None or item.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="work item not found")
    return item


@router.post("/{work_item_id}/assign/human", response_model=ExecutionResponse)
async def assign_human(
    work_item_id: UUID,
    payload: HumanAssignmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = await _get_work_item(db, work_item_id, current_user.tenant_id)
    try:
        UnifiedExecutionService(db).assign_human(item, payload.executor_id)
        await db.commit()
    except ExecutionError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ExecutionResponse(work_item_id=item.id, status=item.status.value, dispatched=False, waiting_for_approval=False)
