from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.deps import DbSession, TenantContext, get_current_context
from app.schemas.admin import AdminDashboardResponse, AdminTenantListResponse
from app.schemas.common import APIResponse
from app.schemas.feedback import ValidationSummaryResponse
from app.services import admin_service, feedback_service, billing_service

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_platform_admin(ctx: TenantContext = Depends(get_current_context)) -> TenantContext:
    if not ctx.user.is_platform_admin:
        raise HTTPException(status_code=403, detail="Platform administrator access required")
    return ctx


PlatformAdminContext = Annotated[TenantContext, Depends(require_platform_admin)]


@router.get("/dashboard", response_model=APIResponse[AdminDashboardResponse])
async def get_dashboard(ctx: PlatformAdminContext, db: DbSession):
    return APIResponse(success=True, data=AdminDashboardResponse.model_validate(await admin_service.dashboard(db)))


@router.get("/tenants", response_model=APIResponse[AdminTenantListResponse])
async def list_tenants(
    ctx: PlatformAdminContext,
    db: DbSession,
    status: str | None = Query(default=None),
):
    data = await admin_service.dashboard(db)
    items = data["tenants_breakdown"]
    if status:
        items = [item for item in items if item["status"] == status]
    return APIResponse(success=True, data=AdminTenantListResponse(items=items))


@router.get("/validation", response_model=APIResponse[ValidationSummaryResponse])
async def get_validation_summary(ctx: PlatformAdminContext, db: DbSession):
    """Phase 3 ('Validation') tracking — see 03_Roadmap_v1.1 §6 and
    app/services/feedback_service.py. Surfaces the roadmap's own exit
    criteria (>=3 tenants regularly running the Report Employee, plus
    recorded qualitative feedback) so the team can judge Phase 3 status
    from real data instead of a spreadsheet."""
    summary = await feedback_service.validation_summary(db)
    return APIResponse(success=True, data=ValidationSummaryResponse.model_validate(summary))


@router.get("/billing")
async def get_billing_summary(ctx: PlatformAdminContext, db: DbSession):
    return APIResponse(success=True, data=await billing_service.platform_mrr(db))
