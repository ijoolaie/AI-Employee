"""Database fence for concurrent Celery Run deliveries."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run import Run
from app.services import run_service


async def execute_run_locked(db: AsyncSession, *, run_id: UUID) -> Run:
    """Acquire the Run row lock before entering RunService execution.

    Celery can deliver the same task more than once. The idempotency check in
    ``run_service.execute_run`` is only safe after one transaction has
    serialized admission and transitioned the Run away from ``pending``.
    Holding this row lock across the call makes the second delivery observe the
    committed ``running``/terminal state instead of racing on a stale
    ``pending`` snapshot.
    """
    result = await db.execute(
        select(Run).where(Run.id == run_id).with_for_update()
    )
    run = result.scalar_one_or_none()
    if run is None:
        # Preserve the canonical service error and lookup semantics.
        return await run_service.execute_run(db, run_id=run_id)

    return await run_service.execute_run(db, run_id=run_id)
