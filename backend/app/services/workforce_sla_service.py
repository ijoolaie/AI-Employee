"""Tenant-owned workforce SLA contract management."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAppError
from app.models.workforce_sla_contract import WorkforceSLAContract
from app.services.audit_service import record


MIN_QUEUE_AGE_SECONDS = 1
MAX_QUEUE_AGE_SECONDS = 30 * 24 * 60 * 60


async def get_contract(db: AsyncSession, *, tenant_id: uuid.UUID) -> WorkforceSLAContract | None:
    return (
        await db.execute(
            select(WorkforceSLAContract).where(WorkforceSLAContract.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()


async def upsert_contract(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    max_queue_age_seconds: int,
    enabled: bool = True,
) -> WorkforceSLAContract:
    if not MIN_QUEUE_AGE_SECONDS <= max_queue_age_seconds <= MAX_QUEUE_AGE_SECONDS:
        raise ValidationAppError(
            "max_queue_age_seconds must be between 1 and 2592000 seconds"
        )

    contract = (
        await db.execute(
            select(WorkforceSLAContract)
            .where(WorkforceSLAContract.tenant_id == tenant_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if contract is None:
        candidate = WorkforceSLAContract(
            tenant_id=tenant_id,
            max_queue_age_seconds=max_queue_age_seconds,
            enabled=enabled,
            effective_from=now,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        # The unique tenant constraint closes the create/create race. Keep the
        # insert inside a savepoint so a concurrent winner cannot poison the
        # caller's outer transaction; then reread the committed winner under
        # the row lock before applying this request's update.
        try:
            async with db.begin_nested():
                db.add(candidate)
                await db.flush()
            contract = candidate
            action = "workforce.sla.created"
        except IntegrityError:
            contract = (
                await db.execute(
                    select(WorkforceSLAContract)
                    .where(WorkforceSLAContract.tenant_id == tenant_id)
                    .with_for_update()
                )
            ).scalar_one_or_none()
            if contract is None:
                raise
            contract.max_queue_age_seconds = max_queue_age_seconds
            contract.enabled = enabled
            contract.effective_from = now
            contract.updated_by_user_id = actor_user_id
            await db.flush()
            action = "workforce.sla.updated"
    else:
        contract.max_queue_age_seconds = max_queue_age_seconds
        contract.enabled = enabled
        contract.effective_from = now
        contract.updated_by_user_id = actor_user_id
        await db.flush()
        action = "workforce.sla.updated"

    await record(
        db,
        action=action,
        actor_id=actor_user_id,
        tenant_id=tenant_id,
        resource_type="workforce_sla_contract",
        resource_id=contract.id,
        metadata={
            "max_queue_age_seconds": max_queue_age_seconds,
            "enabled": enabled,
            "effective_from": now.isoformat(),
        },
    )
    return contract
