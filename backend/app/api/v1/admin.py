from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.deps import DbSession, TenantContext, get_current_context, has_permission
from app.schemas.admin import AdminDashboardResponse, AdminTenantListResponse, AdminOptimizationResponse
from app.schemas.agent_fitness import AgentFitnessResponse
from app.schemas.agent_promotion_evidence import AgentPromotionEvidenceResponse
from app.schemas.agent_version_fitness import AgentVersionFitnessResponse
from app.schemas.capacity_forecast import CapacityForecastResponse
from app.schemas.common import APIResponse
from app.schemas.feedback import ValidationSummaryResponse
from app.schemas.workload_balance import WorkloadBalanceEventResponse
from app.schemas.admin_marketplace import MarketplaceFinancialSummaryResponse, MarketplacePayoutApprovalCreate, MarketplacePayoutApprovalResponse, MarketplacePayoutProposalResponse
from app.services import admin_service, feedback_service, billing_service, optimization_service, agent_fitness, agent_promotion_evidence, agent_version_fitness, workload_balance_history, capacity_forecasting, skill_marketplace_payout_service, skill_marketplace_reporting_service

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_platform_admin(ctx: TenantContext = Depends(get_current_context)) -> TenantContext:
    if not ctx.user.is_platform_admin or ctx.tenant.tenant_kind != "vendor":
        raise HTTPException(status_code=403, detail="Vendor platform administrator access required")
    return ctx


PlatformAdminContext = Annotated[TenantContext, Depends(require_platform_admin)]


async def require_marketplace_payout_approver(
    ctx: TenantContext = Depends(get_current_context),
) -> TenantContext:
    ctx = await require_platform_admin(ctx)
    if not await has_permission(ctx, "skill_marketplace.payout.approve"):
        raise HTTPException(
            status_code=403,
            detail="Missing permission: skill_marketplace.payout.approve",
        )
    return ctx


async def require_marketplace_payout_executor(
    ctx: TenantContext = Depends(get_current_context),
) -> TenantContext:
    ctx = await require_platform_admin(ctx)
    if not await has_permission(ctx, "skill_marketplace.payout.execute"):
        raise HTTPException(
            status_code=403,
            detail="Missing permission: skill_marketplace.payout.execute",
        )
    return ctx


MarketplacePayoutApproverContext = Annotated[TenantContext, Depends(require_marketplace_payout_approver)]
MarketplacePayoutExecutorContext = Annotated[TenantContext, Depends(require_marketplace_payout_executor)]


@router.get("/dashboard", response_model=APIResponse[AdminDashboardResponse])
async def get_dashboard(ctx: PlatformAdminContext, db: DbSession):
    return APIResponse(success=True, data=AdminDashboardResponse.model_validate(await admin_service.dashboard(db)))


@router.get("/tenants", response_model=APIResponse[AdminTenantListResponse])
async def list_tenants(ctx: PlatformAdminContext, db: DbSession, status: str | None = Query(default=None)):
    data = await admin_service.dashboard(db)
    items = data["tenants_breakdown"]
    if status:
        items = [item for item in items if item["status"] == status]
    return APIResponse(success=True, data=AdminTenantListResponse(items=items))


@router.get("/validation", response_model=APIResponse[ValidationSummaryResponse])
async def get_validation_summary(ctx: PlatformAdminContext, db: DbSession):
    summary = await feedback_service.validation_summary(db)
    return APIResponse(success=True, data=ValidationSummaryResponse.model_validate(summary))


@router.post("/marketplace/settlements/{settlement_id}/payout-proposal", response_model=APIResponse[MarketplacePayoutProposalResponse])
async def create_marketplace_payout_proposal(
    settlement_id: UUID,
    ctx: PlatformAdminContext,
    db: DbSession,
):
    proposal = await skill_marketplace_payout_service.create_payout_proposal(
        db,
        settlement_id=settlement_id,
        platform_admin_tenant_id=ctx.tenant.id,
        created_by_user_id=ctx.user.id,
    )
    await db.commit()
    return APIResponse(
        success=True,
        data=MarketplacePayoutProposalResponse.model_validate(proposal),
    )


@router.get("/marketplace/payout-proposals", response_model=APIResponse[list[MarketplacePayoutProposalResponse]])
async def list_marketplace_payout_proposals(
    ctx: PlatformAdminContext,
    db: DbSession,
    status: str | None = Query(default=None),
):
    from app.models.skill_marketplace_payout_proposal import SkillMarketplacePayoutProposalStatus

    parsed_status = None
    if status is not None:
        try:
            parsed_status = SkillMarketplacePayoutProposalStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid payout proposal status") from exc

    proposals = await skill_marketplace_payout_service.list_payout_proposals(
        db,
        platform_admin_tenant_id=ctx.tenant.id,
        status=parsed_status,
    )
    return APIResponse(
        success=True,
        data=[MarketplacePayoutProposalResponse.model_validate(item) for item in proposals],
    )






@router.post(
    "/marketplace/payout-proposals/{proposal_id}/approval",
    response_model=APIResponse[MarketplacePayoutApprovalResponse],
)
async def decide_marketplace_payout_approval(
    proposal_id: UUID,
    payload: MarketplacePayoutApprovalCreate,
    ctx: MarketplacePayoutApproverContext,
    db: DbSession,
):
    approval = await skill_marketplace_payout_service.approve_payout_proposal(
        db,
        proposal_id=proposal_id,
        platform_admin_tenant_id=ctx.tenant.id,
        decided_by_user_id=ctx.user.id,
        decision=payload.decision,
        reason=payload.reason,
    )
    await db.commit()
    return APIResponse(
        success=True,
        data=MarketplacePayoutApprovalResponse.model_validate(approval),
    )


@router.post(
    "/marketplace/payout-proposals/{proposal_id}/execute",
    response_model=APIResponse[MarketplacePayoutProposalResponse],
)
async def execute_marketplace_payout(
    proposal_id: UUID,
    ctx: TenantContext = Depends(require_marketplace_payout_executor),
    db: DbSession = None,
):
    proposal = await skill_marketplace_payout_service.execute_payout_proposal(
        db,
        proposal_id=proposal_id,
        platform_admin_tenant_id=ctx.tenant.id,
        executed_by_user_id=ctx.user.id,
    )
    await db.commit()
    return APIResponse(
        success=True,
        data=MarketplacePayoutProposalResponse.model_validate(proposal),
    )


@router.get("/marketplace/financial-summary", response_model=APIResponse[MarketplaceFinancialSummaryResponse])
async def get_marketplace_financial_summary(
    ctx: PlatformAdminContext,
    db: DbSession,
    seller_tenant_id: UUID | None = Query(default=None),
):
    data = await skill_marketplace_reporting_service.marketplace_financial_summary(
        db,
        platform_admin_tenant_id=ctx.tenant.id,
        seller_tenant_id=seller_tenant_id,
    )
    return APIResponse(
        success=True,
        data=MarketplaceFinancialSummaryResponse.model_validate(data),
    )

@router.get("/billing")
async def get_billing_summary(ctx: PlatformAdminContext, db: DbSession):
    return APIResponse(success=True, data=await billing_service.platform_mrr(db))


@router.get("/optimization", response_model=APIResponse[AdminOptimizationResponse])
async def get_optimization_summary(ctx: PlatformAdminContext, db: DbSession):
    """Return measured monthly unit economics and budget/optimization signals."""
    data = await optimization_service.tenant_optimization_summary(db, tenant_id=ctx.tenant.id)
    return APIResponse(success=True, data=AdminOptimizationResponse.model_validate(data))


@router.get("/agent-fitness", response_model=APIResponse[list[AgentFitnessResponse]])
async def get_agent_fitness(
    ctx: PlatformAdminContext,
    db: DbSession,
    agent_instance_id: UUID | None = Query(default=None),
    window_days: int = Query(default=30, ge=1, le=90),
):
    """Return read-only telemetry-backed Agent fitness for the tenant."""
    data = await agent_fitness.agent_fitness_summary(
        db,
        tenant_id=ctx.tenant.id,
        agent_instance_id=agent_instance_id,
        window_days=window_days,
    )
    return APIResponse(success=True, data=[AgentFitnessResponse.model_validate(item) for item in data])


@router.get("/agent-version-fitness", response_model=APIResponse[list[AgentVersionFitnessResponse]])
async def get_agent_version_fitness(
    ctx: PlatformAdminContext,
    db: DbSession,
    agent_template_id: UUID | None = Query(default=None),
    window_days: int = Query(default=30, ge=1, le=90),
):
    """Return read-only fitness aggregated by tenant-scoped AgentTemplate version."""
    data = await agent_version_fitness.agent_version_fitness_summary(
        db,
        tenant_id=ctx.tenant.id,
        agent_template_id=agent_template_id,
        window_days=window_days,
    )
    return APIResponse(success=True, data=[AgentVersionFitnessResponse.model_validate(item) for item in data])


@router.get("/agent-promotion-evidence", response_model=APIResponse[list[AgentPromotionEvidenceResponse]])
async def get_agent_promotion_evidence(
    ctx: PlatformAdminContext,
    db: DbSession,
    agent_template_id: UUID | None = Query(default=None),
    window_days: int = Query(default=30, ge=1, le=90),
):
    """Return read-only candidate-vs-prior-version promotion evidence."""
    data = await agent_promotion_evidence.agent_promotion_evidence_summary(
        db,
        tenant_id=ctx.tenant.id,
        agent_template_id=agent_template_id,
        window_days=window_days,
    )
    return APIResponse(success=True, data=[AgentPromotionEvidenceResponse.model_validate(item) for item in data])


@router.get("/workload-balance/history", response_model=APIResponse[list[WorkloadBalanceEventResponse]])
async def get_workload_balance_history(
    ctx: PlatformAdminContext,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=200),
    target_agent_instance_id: UUID | None = Query(default=None),
):
    """Return tenant-scoped persisted workload-balancing recommendation evidence."""
    events = await workload_balance_history.list_balance_history(
        db,
        tenant_id=ctx.tenant.id,
        limit=limit,
        target_agent_instance_id=target_agent_instance_id,
    )
    return APIResponse(success=True, data=[WorkloadBalanceEventResponse.model_validate(event) for event in events])


@router.get("/capacity-forecast", response_model=APIResponse[CapacityForecastResponse])
async def get_capacity_forecast(
    ctx: PlatformAdminContext,
    db: DbSession,
    window_days: int = Query(default=30, ge=1, le=90),
    horizon_days: int = Query(default=7, ge=1, le=30),
):
    """Return read-only workforce capacity demand forecasting evidence."""
    data = await capacity_forecasting.capacity_forecast(
        db,
        tenant_id=ctx.tenant.id,
        window_days=window_days,
        horizon_days=horizon_days,
    )
    return APIResponse(success=True, data=CapacityForecastResponse.model_validate(data))
