from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.onboarding import OnboardingResponse, OnboardingUpdate
from app.services import onboarding_service
from fastapi import APIRouter

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

def out(row):
    return OnboardingResponse(current_step=row.current_step, completed_steps=row.completed_steps or [], business_type=row.business_type, setup_data=row.setup_data or {}, completed=row.completed)

@router.get("", response_model=APIResponse[OnboardingResponse])
async def get_onboarding(ctx: CurrentContext, db: DbSession):
    return APIResponse(success=True, data=out(await onboarding_service.get_or_create(db, ctx.tenant_id)))

@router.post("/progress", response_model=APIResponse[OnboardingResponse])
async def update_onboarding(payload: OnboardingUpdate, ctx: CurrentContext, db: DbSession):
    row = await onboarding_service.update(db, ctx.tenant_id, payload.step, payload.business_type, payload.data, payload.complete_step)
    return APIResponse(success=True, data=out(row))
