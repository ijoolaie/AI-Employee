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
from app.services.workflow_execution_lease import heartbeat_workflow_execution_lease
from app.services.tenant_resource_limiter import (
    TenantResourceUnavailableError,
    acquire_tenant_resource,
    release_tenant_resource,
)
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.workflow")


async def _lease_heartbeat_loop(workflow_run_id: uuid.UUID, lease_id: uuid.UUID, lost: asyncio.Event) -> None:
    """Renew the lease from an isolated DB session while the worker executes.

    The execution session may be inside a long-running provider call, so the
    heartbeat must never share its AsyncSession. A heartbeat failure is treated
    as lease loss; the execution task is cancelled by the owner loop and the
    durable recovery path can take over after expiry.
    """
    interval = 20
    try:
        while True:
            await asyncio.sleep(interval)
            async with worker_db_session() as heartbeat_db:
                try:
                    await heartbeat_workflow_execution_lease(
                        heartbeat_db,
                        workflow_run_id=workflow_run_id,
                        lease_id=lease_id,
                    )
                    await heartbeat_db.commit()
                except Exception:
                    await heartbeat_db.rollback()
                    lost.set()
                    logger.exception(
                        "workflow_execution_lease_heartbeat_failed",
                        extra={"workflow_run_id": str(workflow_run_id)},
                    )
                    return
    except asyncio.CancelledError:
        raise


async def _run_async(workflow_run_id: str, tenant_id: str) -> None:
    started = perf_counter()
    workflow_uuid = uuid.UUID(workflow_run_id)
    with span("aiep.workflow.execute", workflow_run_id=workflow_run_id, tenant_id=tenant_id) as current_span:
        async with worker_db_session() as db:
            heartbeat_task: asyncio.Task | None = None
            execution_task: asyncio.Task | None = None
            lost = asyncio.Event()
            try:
                lease_id = await workflow_service.acquire_workflow_execution_lease(
                    db, workflow_run_id=workflow_uuid
                )
                execution_task = asyncio.create_task(
                    workflow_service.execute_workflow(
                        db, workflow_run_id=workflow_uuid, execution_lease_id=lease_id
                    )
                )
                heartbeat_task = asyncio.create_task(
                    _lease_heartbeat_loop(workflow_uuid, lease_id, lost)
                )
                done, _ = await asyncio.wait(
                    {execution_task, heartbeat_task}, return_when=asyncio.FIRST_COMPLETED
                )
                if heartbeat_task in done and lost.is_set() and not execution_task.done():
                    execution_task.cancel()
                    await asyncio.gather(execution_task, return_exceptions=True)
                    raise workflow_service.ValidationAppError("WORKFLOW_EXECUTION_LEASE_LOST")
                run = await execution_task
                if lost.is_set():
                    raise workflow_service.ValidationAppError("WORKFLOW_EXECUTION_LEASE_LOST")
                if str(run.tenant_id) != str(tenant_id):
                    raise ValueError("Worker tenant context does not match Workflow Run tenant")
                await db.commit()
                status = run.status
                WORKFLOW_RUNS.labels(status).inc()
                WORKFLOW_LATENCY.observe(perf_counter() - started)
                if current_span is not None:
                    current_span.set_attribute("workflow.status", status)
            except Exception:
                await db.commit()
                WORKFLOW_RUNS.labels("error").inc()
                WORKFLOW_LATENCY.observe(perf_counter() - started)
                logger.exception(
                    "workflow_execution_failed",
                    extra={"workflow_run_id": workflow_run_id},
                )
                raise
            finally:
                if heartbeat_task is not None:
                    heartbeat_task.cancel()
                    await asyncio.gather(heartbeat_task, return_exceptions=True)


@celery_app.task(name="workflow.execute", bind=True, max_retries=3, default_retry_delay=10)
def execute_workflow_task(self, workflow_run_id: str, tenant_id: str) -> None:
    """Execute a Workflow Run while retaining retry only for admission capacity."""
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
        asyncio.run(_run_async(workflow_run_id, tenant_id))
    finally:
        release_tenant_resource(lease)


async def _parallel_branch_async(branch_id: str) -> None:
    with span("aiep.workflow.parallel_branch", branch_id=branch_id):
        await workflow_service._execute_parallel_branch(uuid.UUID(branch_id))


@celery_app.task(name="workflow.parallel_branch", bind=True, max_retries=3, default_retry_delay=10)
def execute_parallel_branch_task(self, branch_id: str) -> None:
    try:
        asyncio.run(_parallel_branch_async(branch_id))
    except Exception:
        logger.exception("workflow_parallel_branch_failed", extra={"branch_id": branch_id})
        raise
