from fastapi import APIRouter, Header, HTTPException
from app.core.config import get_settings
from app.core.deps import CurrentContext, DbSession
from app.schemas.common import APIResponse
from app.schemas.billing import PlanResponse, SubscriptionResponse, SubscribeRequest, CancelRequest, BillingEventRequest, CheckoutSessionRequest, CheckoutSessionResponse, PortalSessionResponse
from app.services import billing_service, stripe_service

router = APIRouter(prefix="/billing", tags=["billing"])

def _sub_response(sub):
    return SubscriptionResponse(id=str(sub.id), plan=PlanResponse.model_validate(sub.plan, from_attributes=True), status=sub.status, provider=sub.provider, current_period_start=sub.current_period_start, current_period_end=sub.current_period_end, cancel_at_period_end=sub.cancel_at_period_end, canceled_at=sub.canceled_at, trial_ends_at=sub.trial_ends_at)

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

@router.post("/events", response_model=APIResponse[dict])
async def billing_event(payload: BillingEventRequest, db: DbSession, x_billing_webhook_secret: str | None = Header(default=None)):
    secret = get_settings().billing_webhook_secret
    if not secret or x_billing_webhook_secret != secret:
        raise HTTPException(status_code=403, detail="Billing webhook authentication failed")
    tenant_id = __import__("uuid").UUID(payload.tenant_id) if payload.tenant_id else None
    event = await billing_service.record_event(db, tenant_id=tenant_id, provider=payload.provider, provider_event_id=payload.provider_event_id, event_type=payload.event_type, payload=payload.payload, plan_code=payload.plan_code, status=payload.status)
    await db.commit()
    return APIResponse(success=True, data={"event_id": str(event.id), "status": event.status})


# ── Phase 6: real Stripe checkout / self-serve portal ──────────────────
# Closes the Phase 4 commercial exit gate's implementation half; see
# documents/64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md for what is
# and is not proven by this code alone.

@router.post("/checkout", response_model=APIResponse[CheckoutSessionResponse])
async def create_checkout(payload: CheckoutSessionRequest, ctx: CurrentContext, db: DbSession):
    """Returns a real Stripe Checkout Session URL for the given paid plan.
    The frontend redirects the browser to this URL; Stripe hosts the actual
    payment form — card data never touches this backend."""
    url = await stripe_service.create_checkout_session(
        db, tenant_id=ctx.tenant_id, user_id=ctx.user_id, plan_code=payload.plan_code
    )
    await db.commit()
    return APIResponse(success=True, data=CheckoutSessionResponse(checkout_url=url))


@router.post("/portal", response_model=APIResponse[PortalSessionResponse])
async def create_portal(ctx: CurrentContext, db: DbSession):
    """Returns a real Stripe Billing Portal URL so the tenant can manage
    their own subscription (upgrade/downgrade/cancel/payment method) —
    the "clear upgrade path" the Roadmap calls for."""
    url = await stripe_service.create_portal_session(db, tenant_id=ctx.tenant_id)
    await db.commit()
    return APIResponse(success=True, data=PortalSessionResponse(portal_url=url))
