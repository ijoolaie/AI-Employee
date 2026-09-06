"""Tenant-scoped read operations for persisted Employee Runs.

Kept separate from the execution-heavy run service so read APIs cannot depend
on the AI execution implementation details. All queries are explicitly scoped
to the caller's tenant.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.run import Run


async def list_runs(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    employee_id: uuid.UUID | None = None,
) -> list[Run]:
    """Return runs visible to one tenant, newest first.

    ``employee_id`` is an optional tenant-scoped filter used by the employee
    detail surface. The query deliberately includes the tenant predicate even
    when an employee filter is supplied, preventing cross-tenant leakage.
    """
    query = select(Run).where(Run.tenant_id == tenant_id)
    if employee_id is not None:
        query = query.where(Run.employee_id == employee_id)
    query = query.order_by(Run.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_run(
    db: AsyncSession,
    *,
    run_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Run:
    """Return one Run only when it belongs to the caller's tenant."""
    result = await db.execute(
        select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise NotFoundError("Run not found")
    return run
