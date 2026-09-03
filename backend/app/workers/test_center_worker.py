"""Background lifecycle maintenance for Test Center runs."""

from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.core.database import worker_db_session
from app.services.audit_service import record
from app.services.test_center import TestCenterError, TestCenterService
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.test_center")


async def _expire_stale_runs_async() -> int:
    settings = get_settings()
    async with worker_db_session() as db:
        service = TestCenterService(db)
        try:
            expired = await service.expire_stale_runs(
                timeout_seconds=settings.test_center_run_timeout_seconds,
                batch_size=200,
            )
            for run in expired:
                await record(
                    db,
                    action="test_run.expired",
                    actor_type="system",
                    actor_id=None,
                    tenant_id=run.tenant_id,
                    resource_type="test_run",
                    resource_id=run.id,
                    metadata={
                        "correlation_id": str(run.correlation_id),
                        "timeout_seconds": settings.test_center_run_timeout_seconds,
                        "source": "celery_beat",
                    },
                )
            await db.commit()
            return len(expired)
        except TestCenterError:
            await db.rollback()
            raise
        except Exception:
            await db.rollback()
            logger.exception("test_center_expiration_sweep_failed")
            raise


@celery_app.task(name="test_center.expiration_sweep")
def expiration_sweep_task() -> int:
    """Expire stale queued/running runs and return the number transitioned."""
    return asyncio.run(_expire_stale_runs_async())
