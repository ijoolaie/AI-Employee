from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.workflow import Workflow, WorkflowRun, WorkflowStepRun
from app.models.workflow_approval import WorkflowApproval
from app.models.workflow_schedule import WorkflowSchedule
from app.models.workflow_event import WorkflowEventTrigger
from app.models.ai_provider_call import AIProviderCall


async def get_dashboard(db: AsyncSession, *, tenant_id):
    emp_result = await db.execute(
        select(
            func.count(Employee.id),
            func.sum(case((Employee.is_active == True, 1), else_=0)),
        ).where(Employee.tenant_id == tenant_id)
    )
    employee_count, active_employee_count = emp_result.one()

    wf_result = await db.execute(
        select(
            func.count(Workflow.id),
            func.sum(case((Workflow.is_active == True, 1), else_=0)),
        ).where(Workflow.tenant_id == tenant_id)
    )
    workflow_count, active_workflow_count = wf_result.one()

    run_result = await db.execute(
        select(
            func.count(WorkflowRun.id),
            func.sum(case((WorkflowRun.status == "running", 1), else_=0)),
            func.sum(case((WorkflowRun.status == "success", 1), else_=0)),
            func.sum(case((WorkflowRun.status == "failed", 1), else_=0)),
        ).where(WorkflowRun.tenant_id == tenant_id)
    )
    run_counts = run_result.one()

    pending_approvals = await db.scalar(
        select(func.count(WorkflowApproval.id)).where(
            WorkflowApproval.tenant_id == tenant_id,
            WorkflowApproval.status == "pending",
        )
    )
    active_schedules = await db.scalar(
        select(func.count(WorkflowSchedule.id)).where(
            WorkflowSchedule.tenant_id == tenant_id,
            WorkflowSchedule.is_active == True,
        )
    )
    active_webhooks = await db.scalar(
        select(func.count(WorkflowEventTrigger.id)).where(
            WorkflowEventTrigger.tenant_id == tenant_id,
            WorkflowEventTrigger.is_active == True,
        )
    )

    usage = await db.execute(
        select(
            func.count(AIProviderCall.id),
            func.sum(AIProviderCall.prompt_tokens),
            func.sum(AIProviderCall.completion_tokens),
            func.sum(AIProviderCall.cost_usd),
            func.avg(AIProviderCall.latency_ms),
            func.sum(case((AIProviderCall.status == "success", 1), else_=0)),
        ).where(AIProviderCall.tenant_id == tenant_id)
    )
    calls, prompt_tokens, completion_tokens, cost, latency, successful_calls = usage.one()
    calls = int(calls or 0)
    successful_calls = int(successful_calls or 0)

    recent = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.tenant_id == tenant_id)
        .order_by(WorkflowRun.created_at.desc())
        .limit(8)
    )
    recent_runs = []
    for r in recent.scalars().all():
        run_cost = await db.scalar(
            select(func.coalesce(func.sum(AIProviderCall.cost_usd), 0))
            .join(WorkflowStepRun, WorkflowStepRun.employee_run_id == AIProviderCall.run_id)
            .where(
                WorkflowStepRun.workflow_run_id == r.id,
                AIProviderCall.tenant_id == tenant_id,
            )
        )
        recent_runs.append(
            {
                "id": str(r.id),
                "workflow_id": str(r.workflow_id),
                "workflow_version_id": str(r.workflow_version_id),
                "status": r.status,
                "created_at": r.created_at,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
                "total_cost_usd": float(run_cost or 0),
            }
        )

    return {
        "employee_count": int(employee_count or 0),
        "active_employee_count": int(active_employee_count or 0),
        "workflow_count": int(workflow_count or 0),
        "active_workflow_count": int(active_workflow_count or 0),
        "workflow_run_count": int(run_counts[0] or 0),
        "running_workflow_run_count": int(run_counts[1] or 0),
        "successful_workflow_run_count": int(run_counts[2] or 0),
        "failed_workflow_run_count": int(run_counts[3] or 0),
        "pending_approval_count": int(pending_approvals or 0),
        "active_schedule_count": int(active_schedules or 0),
        "active_webhook_count": int(active_webhooks or 0),
        "recent_runs": recent_runs,
        "usage": {
            "calls": calls,
            "successful_calls": successful_calls,
            "failed_calls": calls - successful_calls,
            "prompt_tokens": int(prompt_tokens or 0),
            "completion_tokens": int(completion_tokens or 0),
            "total_tokens": int(prompt_tokens or 0) + int(completion_tokens or 0),
            "cost_usd": float(cost or 0),
            "avg_latency_ms": float(latency or 0),
        },
        "health": {"api": "ok"},
        "generated_at": datetime.now(timezone.utc),
    }
