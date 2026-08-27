from fastapi import APIRouter
from app.core.deps import BillingRefundContext, CurrentContext, DbSession
from app.core.logging import request_id_var
from app.schemas.common import APIResponse
from app.schemas.billing import PlanResponse, SubscriptionResponse, SubscribeRequest, CancelRequest, CheckoutSessionRequest, CheckoutSessionResponse, PortalSessionResponse, RefundRequest, RefundResponse
from app.services import audit_service, billing_service, stripe_service, refund_service

router = APIRouter(prefix="/billing", tags=["billing"])

def _sub_response(sub):
    return SubscriptionResponse(id=str(sub.id), plan=PlanResponse.model_validate(sub.plan, from_attributes=True), status=sub.status, provider=sub.provider, current_period_start=sub.current_period_start, current_period_end=sub.current_period_end, cancel_at_period_end=sub.cancel_at_period_end, canceled_at=sub.canceled_at, trial_ends_at=sub.trial_ends_at)

def _refund_response(row):
    return RefundResponse(
        id=str(row.id), operation=row.operation, provider=row.provider,
        provider_refund_id=row.provider_refund_id,
        provider_payment_intent_id=row.provider_payment_intent_id,
        provider_charge_id=row.provider_charge_id,
        amount_cents=row.amount_cents, currency=row.currency, status=row.status,
        reason=row.reason, failure_reason=row.failure_reason,
        created_at=row.created_at, updated_at=row.updated_at,
    )

@router.get("/plans", response_model=APIResponse[list[PlanResponse]])
async def plans(db: DbSession):
    return APIResponse(success=True, data=[PlanResponse.model_validate(p, from_attributes=True) for p in await billing_service.list_plans(db)])

@router.get("/subscription", response_model=APIResponse[SubscriptionResponse])
async def subscription(ctx: CurrentContext, db: DbSession):
    return APIResponse(success=True, data=_sub_response(await billing_service.get_subscription(db, tenant_id=ctx.tenant_id)))

@router.get("/entitlements", response_model=APIResponse[dict])
async def entitlements(ctx: CurrentContext, db: DbSession):
    sub = await billing_service.get_subscription(db, tenant_id=ctx.tenant_id)
    usage = await billing_service.monthly_usage(db, tenant_id=ctx.tenant_id)
    return APIResponse(success=True, data={"usage": usage, "trial_ends_at": sub.trial_ends_at, "status": sub.status, "plan": PlanResponse.model_validate(sub.plan, from_attributes=True).model_dump()})

@router.post("/subscription", response_model=APIResponse[SubscriptionResponse])
async def subscribe(payload: SubscribeRequest, ctx: CurrentContext, db: DbSession):
    sub = await billing_service.change_plan(db, tenant_id=ctx.tenant_id, plan_code=payload.plan_code, actor_id=ctx.user_id)
    await db.commit(); await db.refresh(sub, ["plan"])
    return APIResponse(success=True, data=_sub_response(sub))

@router.post("/subscription/cancel", response_model=APIResponse[SubscriptionResponse])
async def cancel(payload: CancelRequest, ctx: CurrentContext, db: DbSession):
    sub = await billing_service.cancel_subscription(db, tenant_id=ctx.tenant_id, at_period_end=payload.at_period_end)
    await db.commit(); await db.refresh(sub, ["plan"])
    return APIResponse(success=True, data=_sub_response(sub))

@router.post("/checkout", response_model=APIResponse[CheckoutSessionResponse])
async def create_checkout(payload: CheckoutSessionRequest, ctx: CurrentContext, db: DbSession):
    url = await stripe_service.create_checkout_session(
        db, tenant_id=ctx.tenant_id, user_id=ctx.user_id, plan_code=payload.plan_code
    )
    await db.commit()
    return APIResponse(success=True, data=CheckoutSessionResponse(checkout_url=url))

@router.post("/portal", response_model=APIResponse[PortalSessionResponse])
async def create_portal(ctx: CurrentContext, db: DbSession):
    url = await stripe_service.create_portal_session(db, tenant_id=ctx.tenant_id)
    await db.commit()
    return APIResponse(success=True, data=PortalSessionResponse(portal_url=url))

@router.post("/refunds", response_model=APIResponse[RefundResponse])
async def create_refund(payload: RefundRequest, ctx: BillingRefundContext, db: DbSession):
    row = await refund_service.request_refund(
        db,
        tenant_id=ctx.tenant_id,
        operation=payload.operation,
        payment_intent_id=payload.payment_intent_id,
        amount_cents=payload.amount_cents,
        currency=payload.currency,
        reason=payload.reason,
        idempotency_key=payload.idempotency_key,
    )
    await audit_service.record(
        db,
        action=f"billing.{payload.operation}.requested",
        actor_type="user",
        actor_id=ctx.user_id,
        tenant_id=ctx.tenant_id,
        resource_type="payment_refund",
        resource_id=str(row.id),
        status="success" if row.status != "failed" else "failed",
        request_id=request_id_var.get(),
        metadata={
            "operation": row.operation,
            "payment_intent_id": row.provider_payment_intent_id,
            "provider_refund_id": row.provider_refund_id,
            "amount_cents": row.amount_cents,
            "currency": row.currency,
            "idempotency_key": row.idempotency_key,
        },
    )
    await db.commit()
    return APIResponse(success=True, data=_refund_response(row))

@router.get("/refunds/{refund_id}", response_model=APIResponse[RefundResponse])
async def get_refund(refund_id: str, ctx: CurrentContext, db: DbSession):
    import uuid
    row = await refund_service.get_refund(db, tenant_id=ctx.tenant_id, refund_id=uuid.UUID(refund_id))
    return APIResponse(success=True, data=_refund_response(row))
