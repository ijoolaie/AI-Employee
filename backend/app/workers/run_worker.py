"""Celery task that executes an Employee Run out-of-process."""
from __future__ import annotations

import asyncio
import logging

from app.core.database import worker_db_session
from app.core.telemetry import span
from app.core.exceptions import NotFoundError
from app.services import run_service
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.run")


async def _run_async(run_id: str) -> None:
    with span("aiep.employee_run.execute", run_id=run_id):
        # The enqueue can race the transaction that created the Run.  Retry
        # only that pre-execution lookup; replaying a Run after execution has
        # started could duplicate provider/tool side effects.
        for attempt in range(3):
            async with worker_db_session() as db:
                try:
                    await run_service.execute_run(db, run_id=run_id)
                    await db.commit()
                    return
                except NotFoundError as exc:
                    await db.rollback()
                    if str(exc) != "Run not found" or attempt == 2:
                        logger.exception("run_execution_failed", extra={"run_id": run_id})
                        raise
                    logger.warning(
                        "run_not_visible_yet_retrying",
                        extra={"run_id": run_id, "attempt": attempt + 1},
                    )
                except Exception:
                    await db.commit()
                    logger.exception("run_execution_failed", extra={"run_id": run_id})
                    raise
            await asyncio.sleep(0.5 * (attempt + 1))


@celery_app.task(name="run.execute")
def execute_run_task(run_id: str) -> None:
    """Execute one Run, tolerating only the create/queue visibility race.

    Deliberate Celery retries are not configured here because an exception can
    occur after an external AI/tool side effect. Automatically replaying the
    same Run would therefore risk duplicate provider calls or tool side effects.
    The Run service persists ``failed`` before the exception is re-raised, and
    its idempotency guard makes duplicate deliveries harmless.
    """
    asyncio.run(_run_async(run_id))
