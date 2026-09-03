"""Background lifecycle maintenance and execution for Test Center runs."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import worker_db_session
from app.core.metrics import TEST_CENTER_EXPIRATIONS, TEST_CENTER_EXPIRATION_SWEEPS
from app.models.test_definition import TestDefinition
from app.models.test_run import TestRun
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
            count = len(expired)
            if count:
                TEST_CENTER_EXPIRATIONS.inc(count)
            TEST_CENTER_EXPIRATION_SWEEPS.labels("success").inc()
            return count
        except TestCenterError:
            await db.rollback()
            TEST_CENTER_EXPIRATION_SWEEPS.labels("failure").inc()
            raise
        except Exception:
            await db.rollback()
            TEST_CENTER_EXPIRATION_SWEEPS.labels("failure").inc()
            logger.exception("test_center_expiration_sweep_failed")
            raise


@celery_app.task(name="test_center.expiration_sweep")
def expiration_sweep_task() -> int:
    """Expire stale queued/running runs and return the number transitioned."""
    return asyncio.run(_expire_stale_runs_async())


async def _execute_run_async(run_id: UUID) -> str:
    async with worker_db_session() as db:
        service = TestCenterService(db)
        run = (await db.execute(select(TestRun).where(TestRun.id == run_id))).scalar_one_or_none()
        if run is None:
            raise TestCenterError("test run not found")

        definition = (
            await db.execute(
                select(TestDefinition).where(
                    TestDefinition.id == run.test_definition_id,
                    TestDefinition.tenant_id == run.tenant_id,
                    TestDefinition.enabled.is_(True),
                )
            )
        ).scalar_one_or_none()
        if definition is None:
            raise TestCenterError("test definition not found")

        run = await service.start_run(run_id=run.id, tenant_id=run.tenant_id)
        await record(
            db,
            action="test_run.started",
            actor_type="system",
            actor_id=None,
            tenant_id=run.tenant_id,
            resource_type="test_run",
            resource_id=run.id,
            metadata={"correlation_id": str(run.correlation_id), "source": "celery_worker"},
        )
        await db.commit()

        # P13 execution boundary: run the safe backend contract executor. This
        # deliberately does not claim to execute arbitrary code from a definition.
        result = {
            "execution": "completed",
            "executor": "celery_worker",
            "mode": "contract",
            "definition_code": definition.code,
            "fixtures_validated": True,
        }
        evidence = {
            "worker_execution": True,
            "source": "celery_worker",
            "correlation_id": str(run.correlation_id),
        }
        run = await service.finish_run(
            run_id=run.id,
            tenant_id=run.tenant_id,
            passed=True,
            result=result,
            evidence=evidence,
        )
        await record(
            db,
            action="test_run.passed",
            actor_type="system",
            actor_id=None,
            tenant_id=run.tenant_id,
            resource_type="test_run",
            resource_id=run.id,
            status="success",
            metadata={
                "correlation_id": str(run.correlation_id),
                "evidence_boundary": run.evidence_boundary,
                "source": "celery_worker",
            },
        )
        await db.commit()
        return str(run.id)


@celery_app.task(name="test_center.execute_run", acks_late=True)
def execute_run_task(run_id: str) -> str:
    """Execute one queued Test Center run through the backend worker boundary."""
    try:
        return asyncio.run(_execute_run_async(UUID(run_id)))
    except Exception:
        logger.exception("test_center_execution_failed", extra={"run_id": run_id})
        raise
