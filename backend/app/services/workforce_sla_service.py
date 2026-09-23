"""Tenant-owned workforce SLA contract management."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
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

    contract = await get_contract(db, tenant_id=tenant_id)
    now = datetime.now(timezone.utc)
    if contract is None:
        contract = WorkforceSLAContract(
            tenant_id=tenant_id,
            max_queue_age_seconds=max_queue_age_seconds,
            enabled=enabled,
            effective_from=now,
            created_by_user_id=actor_user_id,
            updated_by_user_id=actor_user_id,
        )
        db.add(contract)
        await db.flush()
        action = "workforce.sla.created"
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
