"""Periodic recovery for Runs abandoned by lost workers."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.database import worker_db_session
from app.models.run import Run
from app.services.run_recovery import STALE_RUN_RECOVERY_SECONDS, recover_stale_run_execution
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.run_recovery")

STALE_RUN_SWEEP_BATCH_SIZE = 100


async def _recover_stale_runs_async() -> int:
    """Recover abandoned running Runs without depending on run.execute redelivery."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=STALE_RUN_RECOVERY_SECONDS)
    recovered = 0

    async with worker_db_session() as db:
        result = await db.execute(
            select(Run)
            .where(
                Run.status == "running",
                Run.started_at.is_not(None),
                Run.started_at <= cutoff,
            )
            .order_by(Run.started_at.asc())
            .limit(STALE_RUN_SWEEP_BATCH_SIZE)
            .with_for_update(skip_locked=True)
        )
        stale_runs = result.scalars().all()

        for run in stale_runs:
            if await recover_stale_run_execution(db, run=run):
                recovered += 1

        await db.commit()

    if recovered:
        logger.warning(
            "stale_run_sweep_recovered_runs",
            extra={"recovered_count": recovered},
        )
    return recovered


@celery_app.task(name="run.stale_sweep")
def recover_stale_runs_task() -> int:
    """Periodically fail closed on Runs abandoned by lost workers."""
    return asyncio.run(_recover_stale_runs_async())
