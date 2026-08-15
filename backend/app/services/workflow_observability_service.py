"""Durable workflow execution observability derived from persisted state."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workflow import WorkflowRun, WorkflowStepRun, WorkflowParallelBranchRun
from app.models.outbox import OutboxMessage
from app.core.exceptions import NotFoundError

async def get_workflow_observability(db: AsyncSession, *, workflow_run_id: uuid.UUID, tenant_id: uuid.UUID) -> dict[str, Any]:
    run_result = await db.execute(select(WorkflowRun).where(WorkflowRun.id == workflow_run_id, WorkflowRun.tenant_id == tenant_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("Workflow run not found")
    step_result = await db.execute(select(WorkflowStepRun).where(WorkflowStepRun.workflow_run_id == run.id).order_by(WorkflowStepRun.position.asc()))
    steps = list(step_result.scalars().all())
    branch_result = await db.execute(select(WorkflowParallelBranchRun).where(WorkflowParallelBranchRun.workflow_run_id == run.id))
    branches = list(branch_result.scalars().all())
    outbox_result = await db.execute(select(OutboxMessage).where(OutboxMessage.tenant_id == tenant_id))
    run_outbox = [m for m in outbox_result.scalars().all() if str((m.payload or {}).get("workflow_run_id", "")) == str(run.id)]
    now = datetime.now(timezone.utc)
    end = run.completed_at or now
    duration_ms = max(0, int((end - run.started_at).total_seconds() * 1000)) if run.started_at else 0
    status_counts: dict[str, int] = {}
    for step in steps:
        status_counts[step.status] = status_counts.get(step.status, 0) + 1
    branch_counts: dict[str, int] = {}
    for branch in branches:
        branch_counts[branch.status] = branch_counts.get(branch.status, 0) + 1
    return {
        "workflow_run_id": run.id,
        "workflow_id": run.workflow_id,
        "status": run.status,
        "duration_ms": duration_ms,
        "steps": {
            "total": len(steps),
            "status_counts": status_counts,
            "attempts": sum(int(s.attempt or 1) for s in steps),
            "retry_count": sum(max(0, int(s.attempt or 1) - 1) for s in steps),
        },
        "parallel": {"branch_total": len(branches), "status_counts": branch_counts},
        "outbox": {
            "total": len(run_outbox),
            "pending": sum(1 for m in run_outbox if m.status == "pending"),
            "processing": sum(1 for m in run_outbox if m.status == "processing"),
            "dispatched": sum(1 for m in run_outbox if m.status == "dispatched"),
        },
        "deadline_at": run.deadline_at,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }
