"""Phase 8.3 WorkItem execution API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.agent_instance import AgentInstance
from app.models.work_item import WorkItem
from app.services.execution_audit import record_execution_event
from app.services.unified_execution import ExecutionError, UnifiedExecutionService

router = APIRouter(prefix="/work-items", tags=["work-items"])


class HumanAssignmentRequest(BaseModel):
    executor_id: UUID


class AgentAssignmentRequest(BaseModel):
    agent_instance_id: UUID


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


def _response(result) -> ExecutionResponse:
    return ExecutionResponse(work_item_id=result.work_item.id, status=result.work_item.status.value, dispatched=result.dispatched, waiting_for_approval=result.waiting_for_approval)


@router.post("/{work_item_id}/assign/human", response_model=ExecutionResponse)
async def assign_human(work_item_id: UUID, payload: HumanAssignmentRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    item = await _get_work_item(db, work_item_id, current_user.tenant_id)
    try:
        UnifiedExecutionService(db).assign_human(item, payload.executor_id)
        await record_execution_event(db, tenant_id=item.tenant_id, work_item_id=item.id, action="work_item.assigned", actor_type="user", actor_id=current_user.id, metadata={"executor_type": "human", "executor_id": str(payload.executor_id)})
        await db.commit()
    except ExecutionError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ExecutionResponse(work_item_id=item.id, status=item.status.value, dispatched=False, waiting_for_approval=False)


@router.post("/{work_item_id}/assign/agent", response_model=ExecutionResponse)
async def assign_agent(work_item_id: UUID, payload: AgentAssignmentRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    item = await _get_work_item(db, work_item_id, current_user.tenant_id)
    agent = await db.get(AgentInstance, payload.agent_instance_id)
    if agent is None or agent.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent instance not found")
    try:
        await UnifiedExecutionService(db).assign_agent(item, agent)
        await record_execution_event(db, tenant_id=item.tenant_id, work_item_id=item.id, action="work_item.assigned", actor_type="user", actor_id=current_user.id, metadata={"executor_type": "agent", "agent_instance_id": str(agent.id)})
        await db.commit()
    except ExecutionError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ExecutionResponse(work_item_id=item.id, status=item.status.value, dispatched=False, waiting_for_approval=False)


@router.post("/{work_item_id}/dispatch", response_model=ExecutionResponse)
async def dispatch(work_item_id: UUID, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    item = await _get_work_item(db, work_item_id, current_user.tenant_id)
    try:
        result = await UnifiedExecutionService(db).dispatch(item)
        action = "work_item.waiting_approval" if result.waiting_for_approval else "work_item.dispatched"
        await record_execution_event(db, tenant_id=item.tenant_id, work_item_id=item.id, action=action, actor_type="user", actor_id=current_user.id, metadata={"status": item.status.value})
        await db.commit()
    except ExecutionError as exc:
        await record_execution_event(db, tenant_id=item.tenant_id, work_item_id=item.id, action="work_item.execution_failed", actor_type="user", actor_id=current_user.id, status="failure", metadata={"error_type": type(exc).__name__})
        await db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _response(result)
