"""HTTP API for tenant-scoped work-item execution controls."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.work_item import WorkItem
from app.services.unified_execution import ExecutionError, UnifiedExecutionService

router = APIRouter(prefix="/work-items", tags=["Work Items"])


class HumanAssignmentRequest(BaseModel):
    executor_id: UUID


class DispatchResponse(BaseModel):
    work_item_id: UUID
    status: str
    dispatched: bool
    waiting_for_approval: bool


def _tenant_work_item(db, work_item_id: UUID, tenant_id: UUID) -> WorkItem:
    item = db.get(WorkItem, work_item_id)
    if item is None or item.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="work item not found")
    return item


@router.post("/{work_item_id}/assign/human", response_model=DispatchResponse)
def assign_human(
    work_item_id: UUID,
    payload: HumanAssignmentRequest,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = _tenant_work_item(db, work_item_id, current_user.tenant_id)
    try:
        UnifiedExecutionService(db).assign_human(item, payload.executor_id)
        db.commit()
    except ExecutionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return DispatchResponse(
        work_item_id=item.id, status=item.status.value, dispatched=False, waiting_for_approval=False
    )


@router.post("/{work_item_id}/dispatch", response_model=DispatchResponse)
def dispatch(
    work_item_id: UUID,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = _tenant_work_item(db, work_item_id, current_user.tenant_id)
    try:
        result = UnifiedExecutionService(db).dispatch(item)
        db.commit()
    except ExecutionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return DispatchResponse(
        work_item_id=item.id,
        status=item.status.value,
        dispatched=result.dispatched,
        waiting_for_approval=result.waiting_for_approval,
    )
