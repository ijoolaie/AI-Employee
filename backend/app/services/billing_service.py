"""Provider-neutral Phase 4 billing and entitlement service.

The persistence model is intentionally provider-neutral: a payment adapter can
translate Stripe/Adyen/etc. webhooks into BillingEventRequest without leaking
provider-specific state into quota enforcement.
"""
from __future__ import annotations
import calendar
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.billing import BillingEvent, BillingPlan, Subscription
from app.models.ai_provider_call import AIProviderCall
from app.models.employee import Employee
from app.models.run import Run
from app.models.workflow import Workflow
from app.services import license_service

PLAN_SEEDS = (
    {"code": "starter", "name": "Starter", "monthly_price_usd": Decimal("0.00"), "monthly_runs": 100, "monthly_tokens": 100_000, "max_employees": 3, "max_workflows": 3, "features": {"priority": "standard"}},
    {"code": "business", "name": "Business", "monthly_price_usd": Decimal("49.00"), "monthly_runs": 2_000, "monthly_tokens": 2_000_000, "max_employees": 20, "max_workflows": 25, "features": {"priority": "standard", "analytics": True}},
    {"code": "professional", "name": "Professional", "monthly_price_usd": Decimal("149.00"), "monthly_runs": 10_000, "monthly_tokens": 10_000_000, "max_employees": 100, "max_workflows": 100, "features": {"priority": "high", "analytics": True, "advanced_workflows": True}},
)

async def ensure_plans(db: AsyncSession) -> None:
    for seed in PLAN_SEEDS:
        existing = (await db.execute(select(BillingPlan).where(BillingPlan.code == seed["code"]))).scalar_one_or_none()
        if existing is None:
            db.add(BillingPlan(**seed))
    await db.flush()

def _period_start(now: datetime) -> datetime:
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

def _period_end(start: datetime) -> datetime:
    last = calendar.monthrange(start.year, start.month)[1]
    return start.replace(day=last, hour=23, minute=59, second=59, microsecond=999999)

async def process_subscription_lifecycle(
    db: AsyncSession,
    *,
    subscription: Subscription,
    now: datetime | None = None,
) -> Subscription:
    """Resolve deterministic subscription lifecycle transitions.

    - expired trials move to past_due;
    - active subscriptions renew into the current calendar period;
    - cancel-at-period-end subscriptions become canceled at period end.
    """
    now = now or datetime.now(timezone.utc)
    changed = False

    if (
        subscription.status == "trialing"
        and subscription.trial_ends_at is not None
        and subscription.trial_ends_at <= now
    ):
        subscription.status = "past_due"
        changed = True

    if (
        subscription.cancel_at_period_end
        and subscription.current_period_end <= now
    ):
        subscription.status = "canceled"
        subscription.cancel_at_period_end = False
        subscription.canceled_at = now
        changed = True
    elif (
        subscription.status == "active"
        and subscription.current_period_end <= now
    ):
        start = _period_start(now)
        subscription.current_period_start = start
        subscription.current_period_end = _period_end(start)
        subscription.canceled_at = None
        changed = True

    if changed:
        await db.flush()

    return subscription


async def ensure_subscription(db: AsyncSession, *, tenant_id: uuid.UUID) -> Subscription:
    result = await db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
    sub = result.scalar_one_or_none()
    if sub:
        return await process_subscription_lifecycle(
            db,
            subscription=sub,
        )
    await ensure_plans(db)
    plan = (await db.execute(select(BillingPlan).where(BillingPlan.code == "starter"))).scalar_one()
    now = datetime.now(timezone.utc)
    trial_ends = now + timedelta(days=14)
    sub = Subscription(tenant_id=tenant_id, plan_id=plan.id, status="trialing", provider="manual", current_period_start=_period_start(now), current_period_end=_period_end(now), trial_ends_at=trial_ends)
    db.add(sub)
    await db.flush()
    return sub

async def get_subscription(db: AsyncSession, *, tenant_id: uuid.UUID) -> Subscription:
    sub = await ensure_subscription(db, tenant_id=tenant_id)
    await db.refresh(sub, ["plan"])
    return sub

async def list_plans(db: AsyncSession) -> list[BillingPlan]:
    await ensure_plans(db)
    result = await db.execute(select(BillingPlan).where(BillingPlan.is_active.is_(True)).order_by(BillingPlan.monthly_price_usd))
    return list(result.scalars().all())

async def change_plan(db: AsyncSession, *, tenant_id: uuid.UUID, plan_code: str, actor_id: uuid.UUID | None) -> Subscription:
    sub = await ensure_subscription(db, tenant_id=tenant_id)
    plan = (await db.execute(select(BillingPlan).where(BillingPlan.code == plan_code, BillingPlan.is_active.is_(True)))).scalar_one_or_none()
    if plan is None:
        raise NotFoundError("Billing plan not found")
    if sub.plan_id == plan.id and sub.status == "active":
        return sub
    if sub.status == "canceled":
        raise ConflictError("Canceled subscription cannot be changed")
    sub.plan_id = plan.id
    sub.status = "active"
    sub.cancel_at_period_end = False
    sub.canceled_at = None

    now = datetime.now(timezone.utc)
    if sub.current_period_end <= now:
        sub.current_period_start = _period_start(now)
        sub.current_period_end = _period_end(sub.current_period_start)

    await db.flush()
    return sub

async def cancel_subscription(db: AsyncSession, *, tenant_id: uuid.UUID, at_period_end: bool) -> Subscription:
    sub = await ensure_subscription(db, tenant_id=tenant_id)
    if at_period_end:
        sub.cancel_at_period_end = True
        sub.canceled_at = None
    else:
        sub.status = "canceled"
        sub.cancel_at_period_end = False
        sub.canceled_at = datetime.now(timezone.utc)
    await db.flush()
    return sub

async def record_event(db: AsyncSession, *, tenant_id: uuid.UUID | None, provider: str, provider_event_id: str, event_type: str, payload: dict, plan_code: str | None = None, status: str | None = None) -> BillingEvent:
    existing = (await db.execute(select(BillingEvent).where(BillingEvent.provider == provider, BillingEvent.provider_event_id == provider_event_id))).scalar_one_or_none()
    if existing:
        return existing
    event = BillingEvent(tenant_id=tenant_id, provider=provider, provider_event_id=provider_event_id, event_type=event_type, payload=payload, status="processed")
    db.add(event)
    await db.flush()
    if tenant_id:
        sub = await ensure_subscription(db, tenant_id=tenant_id)
        if plan_code:
            plan = (await db.execute(select(BillingPlan).where(BillingPlan.code == plan_code))).scalar_one_or_none()
            if plan:
                sub.plan_id = plan.id
        if status in {"active", "past_due", "canceled", "trialing"}:
            sub.status = status
            if status == "canceled":
                sub.canceled_at = datetime.now(timezone.utc)
        await db.flush()
    return event

async def monthly_usage(db: AsyncSession, *, tenant_id: uuid.UUID, now: datetime | None = None) -> dict[str, int]:
    now = now or datetime.now(timezone.utc)
    start = _period_start(now)
    calls = (await db.execute(select(func.count(AIProviderCall.id)).where(AIProviderCall.tenant_id == tenant_id, AIProviderCall.created_at >= start))).scalar_one()
    tokens = (await db.execute(select(func.coalesce(func.sum(AIProviderCall.prompt_tokens + AIProviderCall.completion_tokens), 0)).where(AIProviderCall.tenant_id == tenant_id, AIProviderCall.created_at >= start))).scalar_one()
    runs = (await db.execute(select(func.count(Run.id)).where(Run.tenant_id == tenant_id, Run.created_at >= start))).scalar_one()
    employees = (await db.execute(select(func.count(Employee.id)).where(Employee.tenant_id == tenant_id, Employee.is_active.is_(True)))).scalar_one()
    workflows = (await db.execute(select(func.count(Workflow.id)).where(Workflow.tenant_id == tenant_id, Workflow.is_active.is_(True)))).scalar_one()
    return {"calls": int(calls or 0), "tokens": int(tokens or 0), "runs": int(runs or 0), "employees": int(employees or 0), "workflows": int(workflows or 0)}

async def enforce_run_quota(db: AsyncSession, *, tenant_id: uuid.UUID) -> None:
    # Commercial authorization is checked before any run is admitted.
    await license_service.assert_execution_license(db, tenant_id=tenant_id)
    sub = await get_subscription(db, tenant_id=tenant_id)
    if sub.status not in {"active", "trialing"}:
        raise ConflictError("Subscription is not active")
    usage = await monthly_usage(db, tenant_id=tenant_id)
    if usage["runs"] >= sub.plan.monthly_runs:
        raise ConflictError(f"Monthly run quota exceeded for {sub.plan.code} plan")
    if usage["tokens"] >= sub.plan.monthly_tokens:
        raise ConflictError(f"Monthly token quota exceeded for {sub.plan.code} plan")

async def enforce_employee_quota(db: AsyncSession, *, tenant_id: uuid.UUID) -> None:
    sub = await get_subscription(db, tenant_id=tenant_id)
    usage = await monthly_usage(db, tenant_id=tenant_id)
    if usage["employees"] >= sub.plan.max_employees:
        raise ConflictError(f"Employee quota exceeded for {sub.plan.code} plan")

async def enforce_workflow_quota(db: AsyncSession, *, tenant_id: uuid.UUID) -> None:
    sub = await get_subscription(db, tenant_id=tenant_id)
    usage = await monthly_usage(db, tenant_id=tenant_id)
    if usage["workflows"] >= sub.plan.max_workflows:
        raise ConflictError(f"Workflow quota exceeded for {sub.plan.code} plan")


async def platform_mrr(db: AsyncSession) -> dict[str, object]:
    result = await db.execute(select(Subscription, BillingPlan).join(BillingPlan, BillingPlan.id == Subscription.plan_id).where(Subscription.status == "active"))
    rows = result.all()
    paid = [row for row in rows if row[1].monthly_price_usd > 0]
    return {
        "active_subscriptions": len(rows),
        "paid_subscribers": len(paid),
        "mrr_usd": float(sum((row[1].monthly_price_usd for row in paid), Decimal("0"))),
        "by_plan": {code: sum(1 for _, plan in paid if plan.code == code) for code in ("starter", "business", "professional")},
    }
