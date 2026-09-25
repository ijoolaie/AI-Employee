import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.onboarding import OnboardingProgress
from app.services import audit_service


async def get_or_create(db: AsyncSession, tenant_id: uuid.UUID):
    row = (await db.execute(select(OnboardingProgress).where(OnboardingProgress.tenant_id == tenant_id))).scalar_one_or_none()
    if row:
        return row

    candidate = OnboardingProgress(tenant_id=tenant_id)
    try:
        async with db.begin_nested():
            db.add(candidate)
            await db.flush()
    except IntegrityError:
        row = (await db.execute(select(OnboardingProgress).where(OnboardingProgress.tenant_id == tenant_id))).scalar_one_or_none()
        if row is None:
            raise
    else:
        row = candidate

    await db.refresh(row)
    return row


async def update(db: AsyncSession, tenant_id: uuid.UUID, step: int, business_type: str | None, data: dict, complete_step: bool, actor_id: uuid.UUID | None = None):
    row = await get_or_create(db, tenant_id)
    if business_type:
        row.business_type = business_type
    row.setup_data = {**(row.setup_data or {}), **(data or {})}
    completed = set(row.completed_steps or [])
    if complete_step:
        completed.add(step)
    row.completed_steps = sorted(completed)
    row.current_step = max(row.current_step, min(step + (1 if complete_step else 0), 6))
    row.completed = len(completed) >= 6
    await db.flush()
    await audit_service.record(db, action="onboarding.progress_updated", actor_type="user" if actor_id else "system", actor_id=actor_id, tenant_id=tenant_id, resource_type="onboarding_progress", resource_id=str(row.id), metadata={"step": step, "complete_step": complete_step, "business_type": business_type})
    await db.refresh(row)
    return row
