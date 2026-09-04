"""Celery workers for durable Workflow Runs and parallel branches."""
from __future__ import annotations

import asyncio
import logging
import uuid
from time import perf_counter

from app.core.database import worker_db_session
from app.core.metrics import WORKFLOW_LATENCY, WORKFLOW_RUNS
from app.core.telemetry import span
from app.services import workflow_service
from app.services.tenant_resource_limiter import (
    TenantResourceUnavailableError,
    acquire_tenant_resource,
    release_tenant_resource,
)
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.workflow")


async def _run_async(workflow_run_id: str, tenant_id: str) -> None:
    started = perf_counter()
    with span("aiep.workflow.execute", workflow_run_id=workflow_run_id, tenant_id=tenant_id) as current_span:
        async with worker_db_session() as db:
            try:
                run = await workflow_service.execute_workflow(
                    db, workflow_run_id=uuid.UUID(workflow_run_id)
                )
                if str(run.tenant_id) != str(tenant_id):
                    raise ValueError("Worker tenant context does not match Workflow Run tenant")
                await db.commit()
                status = run.status
                WORKFLOW_RUNS.labels(status).inc()
                WORKFLOW_LATENCY.observe(perf_counter() - started)
                if current_span is not None:
                    current_span.set_attribute("workflow.status", status)
            except Exception:
                await db.rollback()
                WORKFLOW_RUNS.labels("error").inc()
                WORKFLOW_LATENCY.observe(perf_counter() - started)
                logger.exception(
                    "workflow_execution_failed",
                    extra={"workflow_run_id": workflow_run_id},
                )
                raise


@celery_app.task(name="workflow.execute", bind=True, max_retries=3, default_retry_delay=10)
def execute_workflow_task(self, workflow_run_id: str, tenant_id: str) -> None:
    """Execute a Workflow Run only while its tenant owns a resource lease."""
    if not tenant_id:
        raise ValueError("tenant_id is required for workflow.execute")
    try:
        lease = acquire_tenant_resource(tenant_id)
    except TenantResourceUnavailableError as exc:
        raise self.retry(exc=exc, countdown=min(60, 5 * (2 ** self.request.retries)))
    if lease is None:
        raise self.retry(
            exc=RuntimeError("Tenant execution capacity is currently exhausted"),
            countdown=min(60, 5 * (2 ** self.request.retries)),
        )
    try:
        try:
            asyncio.run(_run_async(workflow_run_id, tenant_id))
        except Exception as exc:
            raise self.retry(exc=exc, countdown=min(300, 5 * (2 ** self.request.retries)))
    finally:
        release_tenant_resource(lease)


async def _parallel_branch_async(branch_id: str) -> None:
    with span("aiep.workflow.parallel_branch", branch_id=branch_id):
        await workflow_service._execute_parallel_branch(uuid.UUID(branch_id))


@celery_app.task(name="workflow.parallel_branch", bind=True, max_retries=3, default_retry_delay=10)
def execute_parallel_branch_task(self, branch_id: str) -> None:
    try:
        asyncio.run(_parallel_branch_async(branch_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=min(300, 5 * (2 ** self.request.retries)))
