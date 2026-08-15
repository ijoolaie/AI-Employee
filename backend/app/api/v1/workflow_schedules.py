from __future__ import annotations
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.core.deps import DbSession, WorkflowReadContext, WorkflowWriteContext
from app.schemas.common import APIResponse
from app.schemas.workflow import WorkflowScheduleCreate, WorkflowScheduleResponse, WorkflowScheduleUpdate, WorkflowScheduleListResponse
from app.services import workflow_service
from app.services.workflow_trigger_service import create_schedule, next_cron_time
from app.models.workflow_schedule import WorkflowSchedule
from app.models.workflow import Workflow
from app.services import audit_service
from app.core.middleware import request_id_var

router = APIRouter(tags=["workflow-schedules"])


def _validate_schedule_values(cron_expression: str, timezone_name: str) -> datetime:
    try:
        zone = ZoneInfo(timezone_name)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid timezone: {timezone_name}") from exc
    try:
        return next_cron_time(cron_expression, datetime.now(zone))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/workflow-schedules", response_model=APIResponse[list[WorkflowScheduleListResponse]])
async def list_all_workflow_schedules(ctx: WorkflowReadContext, db: DbSession):
    result = await db.execute(
        select(WorkflowSchedule, Workflow.name)
        .join(Workflow, Workflow.id == WorkflowSchedule.workflow_id)
        .where(WorkflowSchedule.tenant_id == ctx.tenant_id)
        .order_by(WorkflowSchedule.created_at.desc())
        .limit(200)
    )
    data = []
    for schedule, workflow_name in result.all():
        item = WorkflowScheduleListResponse.model_validate(schedule).model_copy(update={"workflow_name": workflow_name})
        data.append(item)
    return APIResponse(success=True, data=data)


@router.post("/workflows/{workflow_id}/schedules", response_model=APIResponse[WorkflowScheduleResponse], status_code=201)
async def create_workflow_schedule(workflow_id: uuid.UUID, payload: WorkflowScheduleCreate, ctx: WorkflowWriteContext, db: DbSession):
    await workflow_service.get_workflow(db, workflow_id=workflow_id, tenant_id=ctx.tenant_id)
    schedule = await create_schedule(db, tenant_id=ctx.tenant_id, workflow_id=workflow_id, cron_expression=payload.cron_expression, timezone_name=payload.timezone, created_by=ctx.user_id)
    return APIResponse(success=True, data=WorkflowScheduleResponse.model_validate(schedule))


@router.get("/workflows/{workflow_id}/schedules", response_model=APIResponse[list[WorkflowScheduleResponse]])
async def list_workflow_schedules(workflow_id: uuid.UUID, ctx: WorkflowReadContext, db: DbSession):
    workflow = await workflow_service.get_workflow(db, workflow_id=workflow_id, tenant_id=ctx.tenant_id)
    result = await db.execute(select(WorkflowSchedule).where(WorkflowSchedule.workflow_id == workflow.id, WorkflowSchedule.tenant_id == ctx.tenant_id).order_by(WorkflowSchedule.created_at.desc()))
    return APIResponse(success=True, data=[WorkflowScheduleResponse.model_validate(x) for x in result.scalars().all()])


@router.patch("/workflow-schedules/{schedule_id}", response_model=APIResponse[WorkflowScheduleResponse])
async def update_workflow_schedule(schedule_id: uuid.UUID, payload: WorkflowScheduleUpdate, ctx: WorkflowWriteContext, db: DbSession):
    result = await db.execute(select(WorkflowSchedule).where(WorkflowSchedule.id == schedule_id, WorkflowSchedule.tenant_id == ctx.tenant_id).with_for_update())
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=404, detail="Workflow schedule not found")

    cron_expression = payload.cron_expression or schedule.cron_expression
    timezone_name = payload.timezone or schedule.timezone
    next_local = _validate_schedule_values(cron_expression, timezone_name)
    schedule.cron_expression = cron_expression
    schedule.timezone = timezone_name
    if payload.is_active is not None:
        schedule.is_active = payload.is_active
    schedule.next_run_at = next_local.astimezone(timezone.utc) if schedule.is_active else None
    await db.flush()
    await audit_service.record(
        db,
        action="workflow.schedule.updated",
        actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        resource_type="workflow_schedule",
        resource_id=schedule.id,
        request_id=request_id_var.get(),
        metadata={"workflow_id": str(schedule.workflow_id), "active": schedule.is_active, "cron": schedule.cron_expression, "timezone": schedule.timezone},
    )
    return APIResponse(success=True, data=WorkflowScheduleResponse.model_validate(schedule))


@router.delete("/workflow-schedules/{schedule_id}", response_model=APIResponse[dict])
async def delete_workflow_schedule(schedule_id: uuid.UUID, ctx: WorkflowWriteContext, db: DbSession):
    result = await db.execute(select(WorkflowSchedule).where(WorkflowSchedule.id == schedule_id, WorkflowSchedule.tenant_id == ctx.tenant_id).with_for_update())
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=404, detail="Workflow schedule not found")
    await audit_service.record(
        db,
        action="workflow.schedule.deleted",
        actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        resource_type="workflow_schedule",
        resource_id=schedule.id,
        request_id=request_id_var.get(),
        metadata={"workflow_id": str(schedule.workflow_id), "cron": schedule.cron_expression, "timezone": schedule.timezone},
    )
    await db.delete(schedule)
    return APIResponse(success=True, data={"deleted": True})
