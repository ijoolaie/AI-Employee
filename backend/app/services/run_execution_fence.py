"""Database fence for concurrent Celery Run deliveries."""
from __future__ import annotations

from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.models.work_item import WorkItem
from app.services import run_service, billing_service, audit_service


async def _lock_work_item_lineage(db: AsyncSession, *, work_item_id: UUID, tenant_id: UUID) -> None:
    """Lock the WorkItem hierarchy root -> leaf before locking its Run.

    Cancellation acquires WorkItem locks from the parent toward descendants
    and only then locks queued Runs. Execution must use the same order before
    retaining the Run lock, otherwise completion can deadlock with cancellation
    (Run -> WorkItem versus WorkItem -> Run).
    """
    lineage_ids: list[UUID] = []
    current_id: UUID | None = work_item_id
    while current_id is not None:
        result = await db.execute(
            select(WorkItem.id, WorkItem.parent_work_item_id)
            .where(
                WorkItem.id == current_id,
                WorkItem.tenant_id == tenant_id,
            )
        )
        row = result.one_or_none()
        if row is None:
            return
        lineage_ids.append(row[0])
        current_id = row[1]

    for item_id in reversed(lineage_ids):
        await db.execute(
            select(WorkItem)
            .where(
                WorkItem.id == item_id,
                WorkItem.tenant_id == tenant_id,
            )
            .with_for_update()
        )


async def execute_run_locked(db: AsyncSession, *, run_id: UUID) -> Run:
    """Acquire WorkItem lineage then Run locks before RunService execution.

    Celery can deliver the same task more than once. The idempotency check in
    run_service.execute_run is only safe after one transaction has serialized
    admission and transitioned the Run away from pending.
    Holding the WorkItem hierarchy and Run locks across the call keeps the
    execution path in the same parent-first order used by cancellation and
    lifecycle projection.
    """
    result = await db.execute(select(Run).where(Run.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        return await run_service.execute_run(db, run_id=run_id)

    if run.work_item_id is not None:
        await _lock_work_item_lineage(
            db,
            work_item_id=run.work_item_id,
            tenant_id=run.tenant_id,
        )

    locked_result = await db.execute(
        select(Run).where(Run.id == run_id).with_for_update()
    )
    locked_run = locked_result.scalar_one_or_none()
    if locked_run is None:
        return await run_service.execute_run(db, run_id=run_id)

    try:
        await billing_service.assert_run_execution_entitlement(
            db,
            tenant_id=locked_run.tenant_id,
        )
    except ConflictError as exc:
        locked_run.status = "failed"
        locked_run.error_message = str(exc)[:2000]
        locked_run.completed_at = datetime.now(timezone.utc)
        await audit_service.record(
            db,
            action="run.execution_entitlement_denied",
            actor_type="system",
            tenant_id=locked_run.tenant_id,
            resource_type="run",
            resource_id=locked_run.id,
            status="failure",
            metadata={"error": locked_run.error_message},
        )
        await db.flush()
        return locked_run

    return await run_service.execute_run(db, run_id=run_id)
