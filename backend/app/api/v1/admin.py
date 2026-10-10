from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.deps import DbSession, TenantContext, get_current_context
from app.schemas.admin import AdminDashboardResponse, AdminTenantListResponse, AdminOptimizationResponse
from app.schemas.agent_fitness import AgentFitnessResponse
from app.schemas.agent_promotion_evidence import AgentPromotionEvidenceResponse
from app.schemas.agent_version_fitness import AgentVersionFitnessResponse
from app.schemas.capacity_forecast import CapacityForecastResponse
from app.schemas.common import APIResponse
from app.schemas.world_commerce import WorldCatalogueAdminWriteRequest, WorldCatalogueItemResponse
from app.models.world_commerce import WorldCatalogueItem
from app.services import audit_service
from app.schemas.feedback import ValidationSummaryResponse
from app.schemas.workload_balance import WorkloadBalanceEventResponse
from app.schemas.admin_marketplace import MarketplaceFinancialSummaryResponse, MarketplacePayoutProposalResponse, MarketplacePayoutReconciliationRequest
from app.services import admin_service, feedback_service, billing_service, optimization_service, agent_fitness, agent_promotion_evidence, agent_version_fitness, workload_balance_history, capacity_forecasting, skill_marketplace_payout_service, skill_marketplace_reporting_service

router = APIRouter(prefix="/admin", tags=["admin"])


async def require_platform_admin(ctx: TenantContext = Depends(get_current_context)) -> TenantContext:
    if not ctx.user.is_platform_admin or ctx.tenant.tenant_kind != "vendor":
        raise HTTPException(status_code=403, detail="Vendor platform administrator access required")
    return ctx


PlatformAdminContext = Annotated[TenantContext, Depends(require_platform_admin)]


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



@router.get("/marketplace/payout-executions", response_model=APIResponse[list[MarketplacePayoutProposalResponse]])
async def list_marketplace_payout_executions(
    ctx: PlatformAdminContext,
    db: DbSession,
    execution_status: str | None = Query(default=None),
    seller_tenant_id: UUID | None = Query(default=None),
):
    from app.models.skill_marketplace_payout_proposal import SkillMarketplacePayoutExecutionStatus

    parsed_status = None
    if execution_status is not None:
        try:
            parsed_status = SkillMarketplacePayoutExecutionStatus(execution_status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid payout execution status") from exc

    proposals = await skill_marketplace_payout_service.list_payout_execution_evidence(
        db,
        platform_admin_tenant_id=ctx.tenant.id,
        execution_status=parsed_status,
        seller_tenant_id=seller_tenant_id,
    )
    return APIResponse(success=True, data=[MarketplacePayoutProposalResponse.model_validate(item) for item in proposals])


@router.post("/marketplace/payout-executions/{proposal_id}/reconcile", response_model=APIResponse[MarketplacePayoutProposalResponse])
async def reconcile_marketplace_payout_execution(
    proposal_id: UUID,
    request: MarketplacePayoutReconciliationRequest,
    ctx: PlatformAdminContext,
    db: DbSession,
):
    if request.proposal_id != proposal_id:
        raise HTTPException(status_code=422, detail="Request proposal_id does not match path proposal_id")
    if request.outcome not in {"accepted", "failed", "unknown"}:
        raise HTTPException(status_code=422, detail="Invalid payout reconciliation outcome")
    proposal = await skill_marketplace_payout_service.reconcile_unknown_payout_execution(
        db,
        proposal_id=proposal_id,
        platform_admin_tenant_id=ctx.tenant.id,
        actor_user_id=ctx.user.id,
        approval_granted=True,
        approval_request_id=request.approval_request_id,
        outcome=request.outcome,
        evidence_ref=request.evidence_ref,
    )
    await db.commit()
    return APIResponse(success=True, data=MarketplacePayoutProposalResponse.model_validate(proposal))


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


@router.get("/world-commerce/catalogue", response_model=APIResponse[list[WorldCatalogueItemResponse]])
async def list_world_catalogue_admin(ctx: PlatformAdminContext, db: DbSession):
    """List active and inactive catalogue items for platform-admin configuration."""
    from sqlalchemy import select

    rows = await db.scalars(select(WorldCatalogueItem).order_by(WorldCatalogueItem.item_type, WorldCatalogueItem.code))
    return APIResponse(success=True, data=[
        WorldCatalogueItemResponse.model_validate(item, from_attributes=True) for item in rows.all()
    ])


@router.post("/world-commerce/catalogue", response_model=APIResponse[WorldCatalogueItemResponse], status_code=201)
async def create_world_catalogue_item(
    payload: WorldCatalogueAdminWriteRequest,
    ctx: PlatformAdminContext,
    db: DbSession,
):
    """Create a catalogue entry; configured providers are labels, not verified integrations."""
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    existing = await db.scalar(select(WorldCatalogueItem.id).where(WorldCatalogueItem.code == payload.code))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Catalogue item code already exists")
    item = WorldCatalogueItem(
        code=payload.code,
        item_type=payload.item_type,
        name=payload.name,
        description=payload.description,
        price_options={currency: option.model_dump(mode="json") for currency, option in payload.price_options.items()},
        is_free=payload.is_free,
        is_active=payload.is_active,
        lease_duration_days=payload.lease_duration_days,
    )
    db.add(item)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Catalogue item code already exists") from exc
    await audit_service.record(
        db, tenant_id=ctx.tenant.id, actor_type="user", actor_id=ctx.user.id,
        action="world.catalogue.created", resource_type="world_catalogue_item",
        resource_id=str(item.id),
        metadata={"code": item.code, "item_type": item.item_type, "currencies": sorted(item.price_options)},
    )
    await db.commit()
    await db.refresh(item)
    return APIResponse(success=True, data=WorldCatalogueItemResponse.model_validate(item, from_attributes=True))


@router.put("/world-commerce/catalogue/{item_id}", response_model=APIResponse[WorldCatalogueItemResponse])
async def replace_world_catalogue_item(
    item_id: UUID,
    payload: WorldCatalogueAdminWriteRequest,
    ctx: PlatformAdminContext,
    db: DbSession,
):
    """Replace catalogue configuration and audit the changed public configuration."""
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError

    item = await db.scalar(select(WorldCatalogueItem).where(WorldCatalogueItem.id == item_id).with_for_update())
    if item is None:
        raise HTTPException(status_code=404, detail="World catalogue item not found")
    duplicate = await db.scalar(select(WorldCatalogueItem.id).where(
        WorldCatalogueItem.code == payload.code, WorldCatalogueItem.id != item_id
    ))
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="Catalogue item code already exists")
    old_code = item.code
    item.code = payload.code
    item.item_type = payload.item_type
    item.name = payload.name
    item.description = payload.description
    item.price_options = {currency: option.model_dump(mode="json") for currency, option in payload.price_options.items()}
    item.is_free = payload.is_free
    item.is_active = payload.is_active
    item.lease_duration_days = payload.lease_duration_days
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Catalogue item code already exists") from exc
    await audit_service.record(
        db, tenant_id=ctx.tenant.id, actor_type="user", actor_id=ctx.user.id,
        action="world.catalogue.updated", resource_type="world_catalogue_item",
        resource_id=str(item.id),
        metadata={"previous_code": old_code, "code": item.code, "item_type": item.item_type,
                  "currencies": sorted(item.price_options)},
    )
    await db.commit()
    await db.refresh(item)
    return APIResponse(success=True, data=WorldCatalogueItemResponse.model_validate(item, from_attributes=True))
