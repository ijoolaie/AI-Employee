"""Periodic dispatchers for workflow schedules and event deliveries."""
from __future__ import annotations
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.database import worker_db_session
from app.services import workflow_service
from app.services.workflow_trigger_service import claim_due_schedules, advance_schedule, dispatch_event
from app.models.workflow_event import WorkflowEventDelivery
from app.workers.celery_app import celery_app
logger = logging.getLogger("app.workers.workflow_trigger")

async def _schedule_tick_async() -> int:
    async with worker_db_session() as db:
        now = datetime.now(timezone.utc)
        schedules = await claim_due_schedules(db, now=now)
        for schedule in schedules:
            run = await workflow_service.create_workflow_run(db, tenant_id=schedule.tenant_id, workflow_id=schedule.workflow_id, input_data={"trigger": "schedule", "schedule_id": str(schedule.id)}, created_by=schedule.created_by)
            await advance_schedule(db, schedule=schedule, run=run, now=now)
            from app.services.outbox_service import enqueue
            await enqueue(db, kind="workflow.execute", tenant_id=schedule.tenant_id, payload={"workflow_run_id": str(run.id)}, dedupe_key=f"workflow.execute:{run.id}:schedule")
        await db.commit()
        return len(schedules)

@celery_app.task(name="workflow.schedule_tick")
def schedule_tick() -> int:
    return asyncio.run(_schedule_tick_async())

async def _event_delivery_async(delivery_id: str) -> None:
    async with worker_db_session() as db:
        delivery = await dispatch_event(db, delivery_id=uuid.UUID(delivery_id))
        if delivery.workflow_run_id:
            from app.services.outbox_service import enqueue
            await enqueue(db, kind="workflow.execute", tenant_id=delivery.tenant_id, payload={"workflow_run_id": str(delivery.workflow_run_id)}, dedupe_key=f"workflow.execute:{delivery.workflow_run_id}:event")
        await db.commit()

@celery_app.task(name="workflow.event_dispatch", bind=True, max_retries=3, default_retry_delay=5)
def event_dispatch(self, delivery_id: str) -> None:
    try:
        asyncio.run(_event_delivery_async(delivery_id))
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(name="workflow.approval_expiry")
def expire_workflow_approvals() -> int:
    import asyncio
    return asyncio.run(_expire_workflow_approvals_async())

async def _expire_workflow_approvals_async() -> int:
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.core.database import worker_db_session
    from app.models.workflow_approval import WorkflowApproval
    from app.models.workflow import WorkflowRun, WorkflowStepRun
    from app.services import audit_service
    count = 0
    async with worker_db_session() as db:
        result = await db.execute(select(WorkflowApproval).where(WorkflowApproval.status == "pending", WorkflowApproval.expires_at.is_not(None), WorkflowApproval.expires_at <= datetime.now(timezone.utc)).with_for_update(skip_locked=True))
        for approval in result.scalars().all():
            approval.status = "expired"
            approval.decided_at = datetime.now(timezone.utc)
            step_result = await db.execute(select(WorkflowStepRun).where(WorkflowStepRun.id == approval.workflow_step_run_id).with_for_update())
            step = step_result.scalar_one_or_none()
            run_result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == approval.workflow_run_id).with_for_update())
            run = run_result.scalar_one_or_none()
            if step and run and run.status == "waiting_approval":
                step.status = "failed"
                step.error = {"code":"WORKFLOW_APPROVAL_EXPIRED","message":"Human approval expired."}
                run.status = "failed"
                run.error = {"step": approval.step_key, **step.error}
                run.completed_at = datetime.now(timezone.utc)
            await audit_service.record(db, action="workflow.approval.expired", actor_type="system", tenant_id=approval.tenant_id, resource_type="workflow_approval", resource_id=approval.id, metadata={"workflow_run_id":str(approval.workflow_run_id),"step_key":approval.step_key})
            count += 1
        await db.commit()
    return count

@celery_app.task(name="workflow.timeout_sweep")
def timeout_workflow_runs() -> int:
    return asyncio.run(_timeout_workflow_runs_async())

async def _timeout_workflow_runs_async() -> int:
    from sqlalchemy import select
    from app.models.workflow import WorkflowRun, WorkflowStepRun
    from app.services import audit_service
    now = datetime.now(timezone.utc)
    count = 0
    async with worker_db_session() as db:
        result = await db.execute(
            select(WorkflowRun).where(
                WorkflowRun.deadline_at.is_not(None),
                WorkflowRun.deadline_at <= now,
                WorkflowRun.status.in_(["pending", "running", "waiting_approval"]),
            ).with_for_update(skip_locked=True)
        )
        for run in result.scalars().all():
            run.status = "timed_out"
            run.completed_at = now
            run.error = {"code": "WORKFLOW_TIMEOUT", "message": "Workflow run exceeded its configured runtime."}
            step_result = await db.execute(select(WorkflowStepRun).where(WorkflowStepRun.workflow_run_id == run.id, WorkflowStepRun.status.in_(["running", "waiting"])).order_by(WorkflowStepRun.position.desc()).limit(1).with_for_update())
            step = step_result.scalar_one_or_none()
            if step:
                step.status = "failed"
                step.error = run.error
                step.completed_at = now
            await audit_service.record(db, action="workflow.run.timed_out", actor_type="system", tenant_id=run.tenant_id, resource_type="workflow_run", resource_id=run.id, status="failure", metadata={"deadline_at": run.deadline_at.isoformat()})
            count += 1
        await db.commit()
    return count
