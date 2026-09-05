"""Tenant-scoped usage, cost and optimization reporting."""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.core.deps import AuditReadContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.cost_anomaly import CostAnomalyForecastResponse
from app.schemas.usage import UsageSummaryResponse
from app.schemas.usage_optimization import UsageOptimizationResponse
from app.services import cost_anomaly_service, optimization_service, usage_service

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/summary", response_model=APIResponse[UsageSummaryResponse])
async def get_usage_summary(
    ctx: AuditReadContext,
    db: DbSession,
    from_at: datetime | None = Query(default=None),
    to_at: datetime | None = Query(default=None),
):
    if from_at is not None and to_at is not None and from_at > to_at:
        raise HTTPException(status_code=422, detail="from_at must be earlier than or equal to to_at")

    data = await usage_service.get_usage_summary(
        db,
        tenant_id=ctx.tenant_id,
        from_at=from_at,
        to_at=to_at,
    )
    return APIResponse(success=True, data=UsageSummaryResponse.model_validate(data))


@router.get("/optimization", response_model=APIResponse[UsageOptimizationResponse])
async def get_usage_optimization(ctx: AuditReadContext, db: DbSession):
    """Return tenant-scoped monthly usage, budget state and optimization guidance."""
    data = await optimization_service.tenant_optimization_summary(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=UsageOptimizationResponse.model_validate(data))


@router.get("/cost-forecast", response_model=APIResponse[CostAnomalyForecastResponse])
async def get_cost_forecast(ctx: AuditReadContext, db: DbSession):
    """Return deterministic daily anomaly detection and month-end cost forecast."""
    data = await cost_anomaly_service.tenant_cost_anomaly_forecast(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=CostAnomalyForecastResponse.model_validate(data))
