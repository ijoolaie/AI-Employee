"""Celery task that executes an Employee Run out-of-process."""
from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from app.agents.memory import build_runtime_memory
from app.agents.runtime import AgentRuntime
from app.agents.runtime_contract import AgentRuntimeContract
from app.core.database import worker_db_session
from app.core.telemetry import span
from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.agent_identity import AgentIdentity
from app.models.employee import EmployeeVersion
from app.models.run import Run
from app.models.tool_approval import ToolApprovalRequest
from app.services import run_service
from app.services.agent_governance import assert_agent_can_execute
from app.services.tenant_resource_limiter import (
    TenantResourceUnavailableError,
    acquire_tenant_resource,
    release_tenant_resource,
)
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.run")


async def _run_async(run_id: str, tenant_id: str) -> None:
    """Execute a Run only when the queued tenant context matches its owner."""
    with span("aiep.employee_run.execute", run_id=run_id, tenant_id=tenant_id):
        async with worker_db_session() as db:
            try:
                parsed_run_id = UUID(run_id)
                parsed_tenant_id = UUID(tenant_id)
            except (ValueError, AttributeError) as exc:
                raise ValidationAppError("Invalid worker tenant/run context") from exc

            result = await db.execute(select(Run).where(Run.id == parsed_run_id))
            run = result.scalar_one_or_none()
            if run is None:
                raise NotFoundError("Run not found")
            if run.tenant_id != parsed_tenant_id:
                raise ValidationAppError(
                    "Worker tenant context does not match Run tenant",
                    details={"run_id": run_id},
                )

            version_result = await db.execute(select(EmployeeVersion).where(EmployeeVersion.id == run.employee_version_id))
            version = version_result.scalar_one_or_none()
            if version is None:
                raise NotFoundError("Employee version not found for this Run")

            # Agent-originated Runs have a first-class identity. Re-check it in
            # the worker, not only at API/dispatch time, because the identity
            # may have been revoked or the instance retired after enqueue.
            if run.agent_instance_id is not None:
                identity_result = await db.execute(
                    select(AgentIdentity).where(
                        AgentIdentity.agent_instance_id == run.agent_instance_id,
                        AgentIdentity.tenant_id == run.tenant_id,
                    )
                )
                identity = identity_result.scalar_one_or_none()
                if identity is None:
                    raise ValidationAppError("Agent Run has no identity")
                # Use the centralized policy boundary for lifecycle + identity
                # checks. A synthetic no-op tool name is intentionally avoided;
                # the governance service exposes lifecycle/identity checks here.
                instance_result = await db.execute(select(AgentIdentity).where(AgentIdentity.id == identity.id))
                if instance_result.scalar_one_or_none() is None:
                    raise ValidationAppError("Agent identity could not be resolved")
                if not identity.active or identity.revoked_at is not None:
                    raise ValidationAppError("Agent Run identity is revoked or inactive")
                from datetime import datetime, timezone
                if identity.expires_at is not None and identity.expires_at <= datetime.now(timezone.utc):
                    identity.active = False
                    await db.flush()
                    raise ValidationAppError("Agent Run identity has expired")

            runtime_memory = await build_runtime_memory(
                db,
                tenant_id=run.tenant_id,
                employee_id=run.employee_id,
                employee_version_id=run.employee_version_id,
                input_data=run.input_data or {},
                rules=version.rules or {},
            )

            approval_result = await db.execute(
                select(ToolApprovalRequest)
                .where(ToolApprovalRequest.run_id == run.id, ToolApprovalRequest.tenant_id == run.tenant_id)
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
                context={"executor": "celery_worker", "agent_instance_id": str(run.agent_instance_id) if run.agent_instance_id else None},
                memory=runtime_memory,
                approval_state=approval_state,
                approval_id=approval_id,
                evidence={
                    "runtime_boundary": "celery_worker",
                    "approval_state": approval_state,
                    "memory_count": len(runtime_memory),
                    "memory_employee_version_id": str(run.employee_version_id),
                    "agent_instance_id": str(run.agent_instance_id) if run.agent_instance_id else None,
                    "agent_identity_id": str(identity.id) if run.agent_instance_id is not None else None,
                },
            )
            contract.validate()
            runtime = AgentRuntime(contract)

            try:
                await runtime.execute(
                    lambda: run_service.execute_run(db, run_id=parsed_run_id),
                    retryable=False,
                )
                refreshed = await db.execute(select(Run).where(Run.id == parsed_run_id))
                completed_run = refreshed.scalar_one_or_none()
                if completed_run is not None:
                    completed_run.total_tokens = int(completed_run.prompt_tokens or 0) + int(completed_run.completion_tokens or 0)
                    await db.flush()
                await db.commit()
            except Exception:
                await db.commit()
                logger.exception("run_execution_failed", extra={"run_id": run_id, "tenant_id": tenant_id})
                raise


@celery_app.task(name="run.execute", bind=True, max_retries=3)
def execute_run_task(self, run_id: str, tenant_id: str) -> None:
    """Execute one Run after acquiring its tenant resource share."""
    if not tenant_id:
        raise ValidationAppError("tenant_id is required for run.execute")
    try:
        lease = acquire_tenant_resource(tenant_id)
    except TenantResourceUnavailableError as exc:
        raise self.retry(exc=exc, countdown=min(60, 5 * (2 ** self.request.retries)))
    if lease is None:
        raise self.retry(exc=RuntimeError("Tenant execution capacity is currently exhausted"), countdown=min(60, 5 * (2 ** self.request.retries)))
    try:
        asyncio.run(_run_async(run_id, tenant_id))
    finally:
        release_tenant_resource(lease)
