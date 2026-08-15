import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.onboarding import OnboardingProgress

async def get_or_create(db: AsyncSession, tenant_id: uuid.UUID):
    row = (await db.execute(select(OnboardingProgress).where(OnboardingProgress.tenant_id == tenant_id))).scalar_one_or_none()
    if row: return row
    row = OnboardingProgress(tenant_id=tenant_id)
    db.add(row); await db.flush(); await db.refresh(row)
    return row

async def update(db: AsyncSession, tenant_id: uuid.UUID, step: int, business_type: str | None, data: dict, complete_step: bool):
    row = await get_or_create(db, tenant_id)
    if business_type: row.business_type = business_type
    row.setup_data = {**(row.setup_data or {}), **(data or {})}
    completed = set(row.completed_steps or [])
    if complete_step: completed.add(step)
    row.completed_steps = sorted(completed)
    row.current_step = max(row.current_step, min(step + (1 if complete_step else 0), 6))
    row.completed = len(completed) >= 6
    await db.flush(); await db.refresh(row)
    return row
