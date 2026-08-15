"""Celery task that executes an Employee Run out-of-process."""
from __future__ import annotations

import asyncio
import logging

from app.core.database import worker_db_session
from app.core.telemetry import span
from app.services import run_service
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.run")


async def _run_async(run_id: str) -> None:
    with span("aiep.employee_run.execute", run_id=run_id):
        async with worker_db_session() as db:
            try:
                await run_service.execute_run(db, run_id=run_id)
                await db.commit()
            except Exception:
                await db.commit()
                logger.exception("run_execution_failed", extra={"run_id": run_id})
                raise


@celery_app.task(name="run.execute")
def execute_run_task(run_id: str) -> None:
    """Execute one Run exactly once from the task's point of view.

    Deliberate Celery retries are not configured here because an exception can
    occur after an external AI/tool side effect. Automatically replaying the
    same Run would therefore risk duplicate provider calls or tool side effects.
    The Run service persists ``failed`` before the exception is re-raised, and
    its idempotency guard makes duplicate deliveries harmless.
    """
    asyncio.run(_run_async(run_id))
