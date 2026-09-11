"""Durable WorkflowRun execution ownership and fencing helpers."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workflow import WorkflowRun
from app.models.workflow_execution_lease import WORKFLOW_EXECUTION_LEASE_DURATION
from app.core.exceptions import ValidationAppError


async def acquire_workflow_execution_lease(db: AsyncSession, *, workflow_run_id: uuid.UUID, allow_recovery: bool = False) -> uuid.UUID:
    """Acquire a lease for a pending/waiting run, or recover an expired running lease."""
    now = datetime.now(timezone.utc)
    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == workflow_run_id).with_for_update())
    run = result.scalar_one_or_none()
    if run is None:
        raise ValidationAppError("Workflow run not found")
    if run.status in {"success", "failed", "cancelled", "timed_out"}:
        raise ValidationAppError("Workflow run is terminal")
    if run.status == "running":
        if not allow_recovery or not run.execution_lease_expires_at or run.execution_lease_expires_at > now:
            raise ValidationAppError("Workflow execution lease is still owned")
    lease_id = uuid.uuid4()
    run.execution_lease_id = lease_id
    run.execution_heartbeat_at = now
    run.execution_lease_expires_at = now + WORKFLOW_EXECUTION_LEASE_DURATION
    if run.status in {"pending", "waiting_approval"}:
        run.status = "running"
    await db.flush()
    return lease_id


async def assert_workflow_execution_lease(db: AsyncSession, *, workflow_run_id: uuid.UUID, lease_id: uuid.UUID) -> WorkflowRun:
    """Fence an owner before it can advance workflow state or create a child."""
    result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == workflow_run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise ValidationAppError("Workflow run not found")
    now = datetime.now(timezone.utc)
    fresh_lease_id = run.execution_lease_id
    if run.status != "running" or fresh_lease_id != lease_id or not run.execution_lease_expires_at or run.execution_lease_expires_at <= now:
        raise ValidationAppError("WORKFLOW_EXECUTION_LEASE_LOST")
    return run


async def heartbeat_workflow_execution_lease(db: AsyncSession, *, workflow_run_id: uuid.UUID, lease_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    updated = await db.execute(update(WorkflowRun).where(WorkflowRun.id == workflow_run_id, WorkflowRun.status == "running", WorkflowRun.execution_lease_id == lease_id, WorkflowRun.execution_lease_expires_at > now).values(execution_heartbeat_at=now, execution_lease_expires_at=now + WORKFLOW_EXECUTION_LEASE_DURATION))
    if updated.rowcount != 1:
        raise ValidationAppError("WORKFLOW_EXECUTION_LEASE_LOST")


async def recover_workflow_execution_lease(db: AsyncSession, *, workflow_run_id: uuid.UUID) -> uuid.UUID:
    """Transfer only an expired running lease; never create a replacement run."""
    return await acquire_workflow_execution_lease(db, workflow_run_id=workflow_run_id, allow_recovery=True)
