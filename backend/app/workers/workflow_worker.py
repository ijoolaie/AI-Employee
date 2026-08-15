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
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.workflow")


async def _run_async(workflow_run_id: str) -> None:
    started = perf_counter()
    with span("aiep.workflow.execute", workflow_run_id=workflow_run_id) as current_span:
        async with worker_db_session() as db:
            try:
                run = await workflow_service.execute_workflow(
                    db, workflow_run_id=uuid.UUID(workflow_run_id)
                )
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
def execute_workflow_task(self, workflow_run_id: str) -> None:
    try:
        asyncio.run(_run_async(workflow_run_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=min(300, 5 * (2 ** self.request.retries)))


async def _parallel_branch_async(branch_id: str) -> None:
    with span("aiep.workflow.parallel_branch", branch_id=branch_id):
        await workflow_service._execute_parallel_branch(uuid.UUID(branch_id))


@celery_app.task(name="workflow.parallel_branch", bind=True, max_retries=3, default_retry_delay=10)
def execute_parallel_branch_task(self, branch_id: str) -> None:
    try:
        asyncio.run(_parallel_branch_async(branch_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=min(300, 5 * (2 ** self.request.retries)))
