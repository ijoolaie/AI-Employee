"""Business order API (Phase 8)."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.order import (
    BusinessOrderCreate,
    BusinessOrderResponse,
    BusinessOrderStatusUpdate,
    OrderSummary,
)
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=APIResponse[list[BusinessOrderResponse]])
async def list_orders(
    ctx: CurrentContext,
    db: DbSession,
    status: str | None = Query(default=None),
):
    rows = await order_service.list_orders(db, tenant_id=ctx.tenant_id, status=status)
    return APIResponse(
        success=True,
        data=[BusinessOrderResponse.model_validate(r) for r in rows],
    )


@router.get("/summary", response_model=APIResponse[OrderSummary])
async def summary(ctx: CurrentContext, db: DbSession):
    data = await order_service.order_summary(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data=OrderSummary.model_validate(data))


@router.get("/{order_id}", response_model=APIResponse[BusinessOrderResponse])
async def get_order(order_id: UUID, ctx: CurrentContext, db: DbSession):
    order = await order_service.get_order(
        db, tenant_id=ctx.tenant_id, order_id=str(order_id)
    )
    return APIResponse(success=True, data=BusinessOrderResponse.model_validate(order))


@router.post(
    "",
    response_model=APIResponse[BusinessOrderResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_order(payload: BusinessOrderCreate, ctx: CurrentContext, db: DbSession):
    order = await order_service.create_order(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user.id,
        customer_name=payload.customer_name,
        line_items=[li.model_dump() for li in payload.line_items],
        currency=payload.currency,
        tax_rate=payload.tax_rate,
        number=payload.number,
        customer_email=payload.customer_email,
        order_date=payload.order_date,
        requested_delivery_date=payload.requested_delivery_date,
        notes=payload.notes,
        source_file_id=str(payload.source_file_id) if payload.source_file_id else None,
        invoice_id=str(payload.invoice_id) if payload.invoice_id else None,
    )
    return APIResponse(success=True, data=BusinessOrderResponse.model_validate(order))


@router.post("/{order_id}/status", response_model=APIResponse[BusinessOrderResponse])
async def update_status(
    order_id: UUID,
    payload: BusinessOrderStatusUpdate,
    ctx: CurrentContext,
    db: DbSession,
):
    order = await order_service.update_status(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user.id,
        order_id=str(order_id),
        status=payload.status,
    )
    await db.refresh(order)
    return APIResponse(success=True, data=BusinessOrderResponse.model_validate(order))


@router.post("/{order_id}/link-invoice", response_model=APIResponse[BusinessOrderResponse])
async def link_invoice(
    order_id: UUID,
    ctx: CurrentContext,
    db: DbSession,
    invoice_id: UUID = Query(...),
):
    order = await order_service.link_invoice(
        db,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user.id,
        order_id=str(order_id),
        invoice_id=str(invoice_id),
    )
    return APIResponse(success=True, data=BusinessOrderResponse.model_validate(order))
