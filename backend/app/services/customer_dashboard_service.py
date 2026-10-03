from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.work_item import WorkItem
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

async def get_office(db: AsyncSession, *, tenant_id):
    """Build a tenant-scoped, read-only presentation state from real Employee/Run data.

    The office layer does not create or mutate execution state. It maps the latest
    governed Run status for each Employee into a small presentation vocabulary.
    """

    # Employee Run records are the authoritative execution state used by the
    # existing workforce runtime. WorkflowStepRun is used only to locate the
    # newest Employee Run without introducing a second state store.
    from app.models.run import Run

    ranked_employee_runs = (
        select(
            Run.id.label("run_id"),
            Run.employee_id.label("employee_id"),
            Run.status.label("run_status"),
            Run.created_at.label("run_created_at"),
            Run.work_item_id.label("work_item_id"),
            func.row_number()
            .over(partition_by=Run.employee_id, order_by=Run.created_at.desc())
            .label("rn"),
        )
        .where(Run.tenant_id == tenant_id)
        .subquery()
    )

    pending_approval_employee_ids = set(
        (
            await db.execute(
                select(WorkflowStepRun.employee_run_id)
                .join(
                    WorkflowApproval,
                    WorkflowApproval.workflow_step_run_id == WorkflowStepRun.id,
                )
                .join(
                    Run,
                    Run.id == WorkflowStepRun.employee_run_id,
                )
                .where(
                    WorkflowApproval.tenant_id == tenant_id,
                    WorkflowApproval.status == "pending",
                    WorkflowStepRun.employee_run_id.is_not(None),
                    Run.tenant_id == tenant_id,
                )
            )
        ).scalars().all()
    )

    pending_approval_result = await db.execute(
        select(
            WorkflowApproval,
            Employee.id.label("employee_id"),
            Employee.name.label("employee_name"),
        )
        .join(
            WorkflowStepRun,
            WorkflowStepRun.id == WorkflowApproval.workflow_step_run_id,
        )
        .outerjoin(
            Run,
            Run.id == WorkflowStepRun.employee_run_id,
        )
        .outerjoin(
            Employee,
            Employee.id == Run.employee_id,
        )
        .where(
            WorkflowApproval.tenant_id == tenant_id,
            WorkflowApproval.status == "pending",
        )
        .order_by(WorkflowApproval.created_at.desc())
        .limit(8)
    )
    pending_approvals = [
        {
            "id": str(approval.id),
            "workflow_run_id": str(approval.workflow_run_id),
            "workflow_step_run_id": str(approval.workflow_step_run_id),
            "employee_id": str(employee_id) if employee_id else None,
            "employee_name": employee_name,
            "step_key": approval.step_key,
            "status": approval.status,
            "created_at": approval.created_at,
            "expires_at": approval.expires_at,
        }
        for approval, employee_id, employee_name in pending_approval_result.all()
    ]

    latest_result = await db.execute(
        select(
            Employee,
            ranked_employee_runs.c.run_id,
            ranked_employee_runs.c.run_status,
            ranked_employee_runs.c.run_created_at,
            ranked_employee_runs.c.work_item_id,
            WorkItem.title.label("work_item_title"),
            WorkItem.status.label("work_item_status"),
        )
        .outerjoin(
            ranked_employee_runs,
            (ranked_employee_runs.c.employee_id == Employee.id)
            & (ranked_employee_runs.c.rn == 1),
        )
        .outerjoin(WorkItem, (WorkItem.id == ranked_employee_runs.c.work_item_id) & (WorkItem.tenant_id == tenant_id))
        .where(Employee.tenant_id == tenant_id)
        .order_by(Employee.created_at.asc(), Employee.name.asc())
    )

    employees = []
    counts = {
        "working": 0,
        "waiting": 0,
        "idle": 0,
        "blocked": 0,
        "escalated": 0,
    }

    for employee, run_id, run_status, run_created_at, work_item_id, work_item_title, work_item_status in latest_result.all():
        if not employee.is_active:
            state = "IDLE"
        elif run_id in pending_approval_employee_ids:
            state = "WAITING_APPROVAL"
        elif run_status in {"pending", "queued", "running"}:
            state = "WORKING"
        elif run_status == "failed":
            state = "ESCALATED"
        elif run_status == "cancelled":
            state = "BLOCKED"
        else:
            state = "IDLE"

        count_key = {
            "WORKING": "working",
            "WAITING_APPROVAL": "waiting",
            "IDLE": "idle",
            "BLOCKED": "blocked",
            "ESCALATED": "escalated",
        }[state]
        counts[count_key] += 1

        current_work_item = None
        if work_item_id and (run_status in {"pending", "queued", "running"} or run_id in pending_approval_employee_ids):
            current_work_item = {
                "id": str(work_item_id),
                "title": work_item_title,
                "status": work_item_status.value if hasattr(work_item_status, "value") else str(work_item_status),
            }

        employees.append(
            {
                "id": str(employee.id),
                "name": employee.name,
                "slug": employee.slug,
                "avatar_url": employee.avatar_url,
                "kind": employee.kind,
                "is_active": employee.is_active,
                "presentation_state": state,
                "latest_run_id": str(run_id) if run_id else None,
                "latest_run_status": run_status,
                "latest_run_created_at": run_created_at,
                "current_work_item": current_work_item,
            }
        )

    return {
        "office_state": "LIVE",
        "employee_count": len(employees),
        "working_count": counts["working"],
        "waiting_count": counts["waiting"],
        "idle_count": counts["idle"],
        "blocked_count": counts["blocked"],
        "escalated_count": counts["escalated"],
        "employees": employees,
        "pending_approvals": pending_approvals,
        "generated_at": datetime.now(timezone.utc),
    }
