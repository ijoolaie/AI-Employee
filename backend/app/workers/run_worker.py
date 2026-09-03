"""Celery task that executes an Employee Run out-of-process."""
from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from app.agents.runtime import AgentRuntime
from app.agents.runtime_contract import AgentRuntimeContract
from app.core.database import worker_db_session
from app.core.telemetry import span
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.run import Run
from app.models.tool_approval import ToolApprovalRequest
from app.services import run_service
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.run")


async def _run_async(run_id: str, tenant_id: str) -> None:
    """Execute a Run only when the queued tenant context matches its owner.

    Tenant identity is carried explicitly in the Celery payload rather than
    being inferred solely from the database record. The worker fails closed
    when the context is missing, malformed, or does not match the Run owner.
    """
    with span("aiep.employee_run.execute", run_id=run_id, tenant_id=tenant_id):
        async with worker_db_session() as db:
            try:
                parsed_run_id = UUID(run_id)
                parsed_tenant_id = UUID(tenant_id)
            except (ValueError, AttributeError) as exc:
                raise ValidationAppError("Invalid worker tenant/run context") from exc

            result = await db.execute(
                select(Run).where(Run.id == parsed_run_id)
            )
            run = result.scalar_one_or_none()
            if run is None:
                raise NotFoundError("Run not found")
            if run.tenant_id != parsed_tenant_id:
                raise ValidationAppError(
                    "Worker tenant context does not match Run tenant",
                    details={"run_id": run_id},
                )

            approval_result = await db.execute(
                select(ToolApprovalRequest)
                .where(
                    ToolApprovalRequest.run_id == run.id,
                    ToolApprovalRequest.tenant_id == run.tenant_id,
                )
                .order_by(ToolApprovalRequest.created_at.desc())
            )
            latest_approval = approval_result.scalars().first()
            approval_state = "granted" if latest_approval is not None and latest_approval.status == "approved" else "not_required"
            approval_id = str(latest_approval.id) if approval_state == "granted" else None

            contract = AgentRuntimeContract(
                tenant_id=str(run.tenant_id),
                run_id=str(run.id),
                employee_id=str(run.employee_id),
                employee_version_id=str(run.employee_version_id),
                input_data=run.input_data or {},
                context={"executor": "celery_worker"},
                approval_state=approval_state,
                approval_id=approval_id,
                evidence={
                    "runtime_boundary": "celery_worker",
                    "approval_state": approval_state,
                },
            )
            runtime = AgentRuntime(contract)

            try:
                await runtime.execute(
                    lambda: run_service.execute_run(db, run_id=parsed_run_id),
                    retryable=False,
                )
                await db.commit()
            except Exception:
                await db.commit()
                logger.exception(
                    "run_execution_failed",
                    extra={"run_id": run_id, "tenant_id": tenant_id},
                )
                raise


@celery_app.task(name="run.execute")
def execute_run_task(run_id: str, tenant_id: str) -> None:
    """Execute one Run with an explicit, validated tenant context.

    Deliberate Celery retries are not configured here because an exception can
    occur after an external AI/tool side effect. Automatically replaying the
    same Run would therefore risk duplicate provider calls or tool side effects.
    The runtime therefore defaults to one attempt for the complete Run.
    """
    if not tenant_id:
        raise ValidationAppError("tenant_id is required for run.execute")
    asyncio.run(_run_async(run_id, tenant_id))
