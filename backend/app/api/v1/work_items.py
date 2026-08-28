"""Phase 8.3 WorkItem execution API."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_context
from app.models.agent_instance import AgentInstance
from app.models.audit_log import AuditLog
from app.models.work_item import WorkItem
from app.services.agent_execution_adapter import AgentExecutionAdapter
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


class ExecutionHistoryItem(BaseModel):
    id: UUID
    action: str
    actor_type: str
    actor_id: UUID | None
    status: str
    request_id: str | None
    metadata: dict
    created_at: object


async def _get_work_item(db: AsyncSession, work_item_id: UUID, tenant_id: UUID) -> WorkItem:
    item = await db.get(WorkItem, work_item_id)
    if item is None or item.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="work item not found")
    return item


def _response(result) -> ExecutionResponse:
    return ExecutionResponse(work_item_id=result.work_item.id, status=result.work_item.status.value, dispatched=result.dispatched, waiting_for_approval=result.waiting_for_approval)


@router.get("/{work_item_id}/history", response_model=list[ExecutionHistoryItem])
async def history(work_item_id: UUID, limit: int = Query(default=100, ge=1, le=200), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_context)):
    await _get_work_item(db, work_item_id, current_user.tenant_id)
    stmt = (
        select(AuditLog)
        .where(AuditLog.tenant_id == current_user.tenant_id, AuditLog.resource_type == "work_item", AuditLog.resource_id == str(work_item_id))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [ExecutionHistoryItem(id=e.id, action=e.action, actor_type=e.actor_type, actor_id=e.actor_id, status=e.status, request_id=e.request_id, metadata=e.metadata_ or {}, created_at=e.created_at) for e in result.scalars().all()]


@router.post("/{work_item_id}/assign/human", response_model=ExecutionResponse)
async def assign_human(work_item_id: UUID, payload: HumanAssignmentRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_context)):
    item = await _get_work_item(db, work_item_id, current_user.tenant_id)
    try:
        UnifiedExecutionService(db).assign_human(item, payload.executor_id)
        await record_execution_event(db, tenant_id=item.tenant_id, work_item_id=item.id, action="work_item.assigned", actor_type="user", actor_id=current_user.user_id, metadata={"executor_type": "human", "executor_id": str(payload.executor_id)})
        await db.commit()
    except ExecutionError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ExecutionResponse(work_item_id=item.id, status=item.status.value, dispatched=False, waiting_for_approval=False)


@router.post("/{work_item_id}/assign/agent", response_model=ExecutionResponse)
async def assign_agent(work_item_id: UUID, payload: AgentAssignmentRequest, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_context)):
    item = await _get_work_item(db, work_item_id, current_user.tenant_id)
    agent = await db.get(AgentInstance, payload.agent_instance_id)
    if agent is None or agent.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent instance not found")
    try:
        await UnifiedExecutionService(db).assign_agent(item, agent)
        await record_execution_event(db, tenant_id=item.tenant_id, work_item_id=item.id, action="work_item.assigned", actor_type="user", actor_id=current_user.user_id, metadata={"executor_type": "agent", "agent_instance_id": str(agent.id)})
        await db.commit()
    except ExecutionError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return ExecutionResponse(work_item_id=item.id, status=item.status.value, dispatched=False, waiting_for_approval=False)


@router.post("/{work_item_id}/dispatch", response_model=ExecutionResponse)
async def dispatch(work_item_id: UUID, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_context)):
    item = await _get_work_item(db, work_item_id, current_user.tenant_id)
    agent_executor = AgentExecutionAdapter(db) if item.executor_type is not None and item.executor_type.value == "agent" else None
    try:
        result = await UnifiedExecutionService(db, agent_executor=agent_executor).dispatch(item)
        action = "work_item.waiting_approval" if result.waiting_for_approval else "work_item.dispatched"
        await record_execution_event(db, tenant_id=item.tenant_id, work_item_id=item.id, action=action, actor_type="user", actor_id=current_user.user_id, metadata={"status": item.status.value, **(item.output_data or {})})
        await db.commit()
    except ExecutionError as exc:
        await record_execution_event(db, tenant_id=item.tenant_id, work_item_id=item.id, action="work_item.execution_failed", actor_type="user", actor_id=current_user.user_id, status="failure", metadata={"error_type": type(exc).__name__})
        await db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _response(result)
