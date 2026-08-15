"""Durable transactional-outbox dispatcher."""
from __future__ import annotations

import asyncio
import logging

from app.core.database import worker_db_session
from app.core.metrics import OUTBOX_DEAD, OUTBOX_DISPATCH, OUTBOX_RETRIES
from app.core.telemetry import span
from app.services import outbox_service
from app.workers.celery_app import celery_app

logger = logging.getLogger("app.workers.outbox")


async def _dispatch_async(limit: int = 50) -> int:
    dispatched = 0
    async with worker_db_session() as db:
        rows = await outbox_service.claim(db, limit=limit)
        for row in rows:
            with span("aiep.outbox.dispatch", outbox_id=str(row.id), kind=row.kind, attempt=row.attempts) as current_span:
                try:
                    if row.kind == "workflow.execute":
                        from app.workers.workflow_worker import execute_workflow_task
                        execute_workflow_task.delay(row.payload["workflow_run_id"])
                    elif row.kind == "workflow.event_dispatch":
                        from app.workers.workflow_trigger_worker import event_dispatch
                        event_dispatch.delay(row.payload["delivery_id"])
                    elif row.kind == "workflow.parallel_branch":
                        from app.workers.workflow_worker import execute_parallel_branch_task
                        execute_parallel_branch_task.delay(row.payload["branch_id"])
                    elif row.kind == "email.send":
                        from app.workers.email_worker import send_email_task
                        send_email_task.delay(str(row.id))
                        await db.commit()
                        OUTBOX_DISPATCH.labels("queued", row.kind).inc()
                        if current_span is not None:
                            current_span.set_attribute("outbox.status", "queued")
                        continue
                    else:
                        raise RuntimeError(f"Unknown outbox kind: {row.kind}")

                    await outbox_service.mark_dispatched(db, row)
                    await db.commit()
                    OUTBOX_DISPATCH.labels("success", row.kind).inc()
                    dispatched += 1
                    if current_span is not None:
                        current_span.set_attribute("outbox.status", "dispatched")
                except Exception as exc:
                    OUTBOX_DISPATCH.labels("error", row.kind).inc()
                    logger.exception(
                        "outbox_dispatch_failed",
                        extra={"outbox_id": str(row.id), "kind": row.kind},
                    )
                    await db.rollback()
                    result = await db.get(type(row), row.id)
                    if result is not None:
                        previous_attempts = result.attempts
                        await outbox_service.mark_retry(
                            db,
                            result,
                            str(exc),
                            delay_seconds=min(300, 5 * max(1, result.attempts)),
                        )
                        if result.status == "dead":
                            OUTBOX_DEAD.labels(result.kind).inc()
                        else:
                            OUTBOX_RETRIES.labels(result.kind).inc()
                        if current_span is not None:
                            current_span.set_attribute("outbox.status", result.status)
                            current_span.set_attribute("outbox.attempts", previous_attempts)
                    await db.commit()
    return dispatched


@celery_app.task(name="outbox.dispatch")
def dispatch_outbox() -> int:
    return asyncio.run(_dispatch_async())
