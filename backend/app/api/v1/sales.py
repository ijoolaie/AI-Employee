"""Sales deals API (Phase 9)."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.deal import (
    BusinessDealCreate,
    BusinessDealResponse,
    BusinessDealStageUpdate,
    SalesForecast,
    SalesPipelineSummary,
)
from app.services import sales_service

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("/deals", response_model=APIResponse[list[BusinessDealResponse]])
async def list_deals(
    ctx: CurrentContext,
    db: DbSession,
    stage: str | None = Query(default=None),
):
    rows = await sales_service.list_deals(db, tenant_id=ctx.tenant_id, stage=stage)
    return APIResponse(
        success=True,
        data=[BusinessDealResponse.model_validate(r) for r in rows],
    )


@router.get("/pipeline", response_model=APIResponse[SalesPipelineSummary])
async def pipeline(ctx: CurrentContext, db: DbSession):
    data = await sales_service.pipeline_summary(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=SalesPipelineSummary.model_validate(data))


@router.get("/forecast", response_model=APIResponse[SalesForecast])
async def forecast(
    ctx: CurrentContext,
    db: DbSession,
    horizon_days: int = Query(default=30, ge=1, le=365),
):
    data = await sales_service.simple_forecast(
        db, tenant_id=ctx.tenant_id, horizon_days=horizon_days
    )
    return APIResponse(success=True, data=SalesForecast.model_validate(data))


@router.get("/deals/{deal_id}", response_model=APIResponse[BusinessDealResponse])
async def get_deal(deal_id: UUID, ctx: CurrentContext, db: DbSession):
    deal = await sales_service.get_deal(
        db, tenant_id=ctx.tenant_id, deal_id=str(deal_id)
    )
    return APIResponse(success=True, data=BusinessDealResponse.model_validate(deal))


@router.post(
    "/deals",
    response_model=APIResponse[BusinessDealResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_deal(payload: BusinessDealCreate, ctx: CurrentContext, db: DbSession):
    deal = await sales_service.create_deal(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user.id,
        title=payload.title,
        customer_name=payload.customer_name,
        amount=payload.amount,
        currency=payload.currency,
        stage=payload.stage,
        probability=payload.probability,
        customer_email=payload.customer_email,
        expected_close_date=payload.expected_close_date,
        owner_name=payload.owner_name,
        notes=payload.notes,
        source=payload.source,
        order_id=str(payload.order_id) if payload.order_id else None,
    )
    return APIResponse(success=True, data=BusinessDealResponse.model_validate(deal))


@router.post("/deals/{deal_id}/stage", response_model=APIResponse[BusinessDealResponse])
async def update_stage(
    deal_id: UUID,
    payload: BusinessDealStageUpdate,
    ctx: CurrentContext,
    db: DbSession,
):
    deal = await sales_service.update_stage(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user.id,
        deal_id=str(deal_id),
        stage=payload.stage,
        probability=payload.probability,
    )
    return APIResponse(success=True, data=BusinessDealResponse.model_validate(deal))
