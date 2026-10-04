"""Stripe payment-provider adapter (Phase 6 — closing the Phase 4 commercial exit gate).

`app/services/billing_service.py` is deliberately provider-neutral (see its
module docstring): quota enforcement, MRR reporting, and the Subscription/
BillingEvent models know nothing about Stripe. This module is the adapter
that connects real Stripe Checkout/Billing-Portal/webhooks to that
provider-neutral core, without changing any of it.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.billing import BillingEvent, BillingPlan, Subscription
from app.models.workforce_revenue_event import WorkforceRevenueEvent
from app.models.tenant import Tenant
from app.models.user import User
from app.services import billing_service

logger = logging.getLogger(__name__)


class StripeNotConfiguredError(ValidationAppError):
    def __init__(self) -> None:
        super().__init__(
            "Stripe is not configured on this deployment. Set STRIPE_SECRET_KEY, "
            "STRIPE_WEBHOOK_SECRET, and STRIPE_PRICE_MAP before using real checkout."
        )


STRIPE_SUBSCRIPTION_LIFECYCLE_EVENTS = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.payment_failed",
}


def _client():
    settings = get_settings()
    if not settings.stripe_enabled:
        raise StripeNotConfiguredError()
    import stripe

    stripe.api_key = settings.stripe_secret_key
    return stripe


def _plan_code_for_price_id(price_id: str) -> str | None:
    settings = get_settings()
    for code, mapped_price_id in settings.stripe_price_map.items():
        if mapped_price_id == price_id:
            return code
    return None


async def _get_or_create_stripe_customer(
    db: AsyncSession,
    stripe,
    *,
    tenant_id: uuid.UUID,
    sub: Subscription,
    user_email: str | None,
) -> str:
    # Stripe Search is eventually consistent and the provider idempotency key
    # can expire. Serialize identity resolution on the durable Subscription row
    # so concurrent workers cannot both observe a missing local customer and
    # race into provider-side creation/reconciliation.
    locked_sub = (
        await db.execute(
            select(Subscription).where(Subscription.id == sub.id).with_for_update()
        )
    ).scalar_one()
    if locked_sub.provider_customer_id:
        return locked_sub.provider_customer_id

    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    tenant_ref = str(tenant_id)

    # Stripe Customer Search provides durable reconciliation after the
    # provider idempotency key has expired, but is eventually consistent.
    search = getattr(stripe.Customer, "search", None)
    if search is not None:
        matches = search(
            query=f"metadata['tenant_id']:'{tenant_ref}'",
            limit=2,
        )
        customers = list(getattr(matches, "data", []) or [])
        if len(customers) > 1:
            raise ConflictError("Multiple Stripe customers are associated with this tenant")
        if len(customers) == 1:
            locked_sub.provider_customer_id = customers[0].id
            await db.flush()
            return customers[0].id

    customer = stripe.Customer.create(
        email=user_email,
        name=tenant.name if tenant else None,
        metadata={"tenant_id": tenant_ref},
        # Customer identity belongs to the tenant, not to an individual
        # checkout attempt. This remains stable across retries with a new
        # checkout idempotency key.
        idempotency_key=f"customer:{tenant_id}",
    )
    locked_sub.provider_customer_id = customer.id
    await db.flush()
    return customer.id


async def create_checkout_session(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    plan_code: str,
    idempotency_key: str,
) -> str:
    """Create a Stripe Checkout Session with caller-supplied idempotency.

    The same key must be reused by the caller when retrying an ambiguous
    request. Stripe then returns the original result instead of creating a
    second Checkout Session after a timeout/crash.
    """
    stripe = _client()
    settings = get_settings()
    price_id = settings.stripe_price_map.get(plan_code)
    if not price_id:
        raise ValidationAppError(
            f"Plan '{plan_code}' has no Stripe Price ID configured in STRIPE_PRICE_MAP; "
            "it may be a free plan not intended to go through Checkout."
        )
    plan = (
        await db.execute(select(BillingPlan).where(BillingPlan.code == plan_code, BillingPlan.is_active.is_(True)))
    ).scalar_one_or_none()
    if plan is None:
        raise NotFoundError("Billing plan not found")
    sub = await billing_service.ensure_subscription(db, tenant_id=tenant_id)
    user = (
        await db.execute(
            select(User).where(User.id == user_id, User.tenant_id == tenant_id)
        )
    ).scalar_one_or_none()
    if user is None:
        raise NotFoundError("Checkout user not found")
    customer_id = await _get_or_create_stripe_customer(
        db,
        stripe,
        tenant_id=tenant_id,
        sub=sub,
        user_email=user.email if user else None,
    )
    trial_days = 0
    if sub.status == "trialing" and sub.trial_ends_at:
        remaining_seconds = (sub.trial_ends_at - datetime.now(timezone.utc)).total_seconds()
        trial_days = max(0, int(remaining_seconds // 86400))
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.stripe_checkout_success_url,
        cancel_url=settings.stripe_checkout_cancel_url,
        client_reference_id=str(tenant_id),
        metadata={"tenant_id": str(tenant_id), "plan_code": plan_code},
        subscription_data={"metadata": {"tenant_id": str(tenant_id), "plan_code": plan_code}, "trial_period_days": trial_days},
        idempotency_key=idempotency_key,
    )
    return session.url


async def create_portal_session(db: AsyncSession, *, tenant_id: uuid.UUID) -> str:
    stripe = _client()
    settings = get_settings()
    sub = await billing_service.ensure_subscription(db, tenant_id=tenant_id)
    if not sub.provider_customer_id:
        raise ConflictError(
            "No Stripe customer on file for this tenant yet — complete a Checkout session first."
        )
    portal = stripe.billing_portal.Session.create(
        customer=sub.provider_customer_id,
        return_url=settings.stripe_portal_return_url,
    )
    return portal.url


def verify_and_parse_webhook(raw_body: bytes, sig_header: str | None):
    stripe = _client()
    settings = get_settings()
    try:
        return stripe.Webhook.construct_event(raw_body, sig_header, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise ValidationAppError("Invalid Stripe webhook signature or payload") from exc


async def create_refund(
    *,
    payment_intent_id: str,
    amount_cents: int | None,
    reason: str | None,
    idempotency_key: str,
) -> dict:
    """Create a Stripe refund against a captured PaymentIntent.

    Stripe's idempotency key makes retries safe even if the worker or HTTP
    client times out after Stripe has accepted the refund request.
    """
    stripe = _client()
    params = {"payment_intent": payment_intent_id, "metadata": {"refund_idempotency_key": idempotency_key}}
    if amount_cents is not None:
        params["amount"] = amount_cents
    if reason in {"duplicate", "fraudulent", "requested_by_customer"}:
        params["reason"] = reason
    refund = stripe.Refund.create(**params, idempotency_key=idempotency_key)
    return {
        "id": refund.id,
        "status": refund.status,
        "amount": refund.amount,
        "currency": refund.currency,
        "charge": refund.charge,
    }


async def create_reversal(*, payment_intent_id: str, idempotency_key: str) -> dict:
    """Cancel an uncaptured PaymentIntent as the provider-side reversal path."""
    stripe = _client()
    payment_intent = stripe.PaymentIntent.cancel(payment_intent_id, idempotency_key=idempotency_key)
    return {"id": payment_intent.id, "status": payment_intent.status}


async def _latest_lifecycle_event_created(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
) -> int:
    """Return the newest persisted Stripe lifecycle event creation time.

    The existing BillingEvent schema predates Stripe ordering protection and
    does not have a dedicated provider-created column. New Stripe events store
    the immutable provider `created` timestamp in the payload. Older rows have
    no timestamp and are ignored for ordering comparisons.
    """
    result = await db.execute(
        select(BillingEvent.payload).where(
            BillingEvent.provider == "stripe",
            BillingEvent.tenant_id == tenant_id,
            BillingEvent.event_type.in_(STRIPE_SUBSCRIPTION_LIFECYCLE_EVENTS),
        )
    )
    latest = 0
    for payload in result.scalars().all():
        try:
            latest = max(latest, int((payload or {}).get("stripe_event_created_at") or 0))
        except (TypeError, ValueError):
            continue
    return latest


async def _lock_subscription_for_lifecycle(
    db: AsyncSession,
    *,
    subscription_id: uuid.UUID,
    event_created_at: int,
) -> tuple[Subscription, bool]:
    """Lock subscription state and reject an older provider lifecycle event."""
    sub = (
        await db.execute(
            select(Subscription).where(Subscription.id == subscription_id).with_for_update()
        )
    ).scalar_one()
    latest = await _latest_lifecycle_event_created(db, tenant_id=sub.tenant_id)
    return sub, bool(event_created_at and latest >= event_created_at)


async def apply_verified_sales_payment(
    db: AsyncSession,
    *,
    provider: str,
    provider_event_id: str,
    data: dict,
) -> tuple[uuid.UUID | None, str | None]:
    """Convert a verified one-time provider payment into a tenant-scoped order.

    The BusinessDeal row is locked so retries/concurrent provider events cannot
    create duplicate business orders. BillingEvent remains the provider webhook
    admission ledger; WorkforceRevenueEvent is the independent, governed business
    outcome boundary used for AI Workforce revenue accounting.
    """
    metadata = data.get("metadata") or {}
    tenant_ref = metadata.get("tenant_id")
    deal_ref = metadata.get("sales_deal_id")
    if not tenant_ref or not deal_ref:
        raise ValidationAppError("Sales payment event is missing tenant/deal correlation metadata")
    try:
        tenant_id = uuid.UUID(str(tenant_ref))
        deal_id = uuid.UUID(str(deal_ref))
    except ValueError as exc:
        raise ValidationAppError("Sales payment event contains invalid tenant/deal correlation") from exc

    from app.models.business_deal import BusinessDeal
    from app.models.business_order import BusinessOrder
    from app.services.workforce_sales_payment_provider import _major_units

    deal = (
        await db.execute(
            select(BusinessDeal).where(
                BusinessDeal.id == deal_id,
                BusinessDeal.tenant_id == tenant_id,
            ).with_for_update()
        )
    ).scalar_one_or_none()
    if deal is None:
        raise NotFoundError("Sales payment references an unknown deal")
    if deal.stage == "lost":
        raise ConflictError("Sales payment cannot settle a lost deal")

    deal_metadata = dict(deal.metadata_ or {})

    # Provider event IDs are globally unique within a provider. Check the
    # independent revenue ledger before the deal-local replay marker so a
    # provider reference cannot settle a second deal without creating a
    # second ledger row.
    existing_revenue_event = (
        await db.execute(
            select(WorkforceRevenueEvent).where(
                WorkforceRevenueEvent.provider == provider,
                WorkforceRevenueEvent.provider_event_id == provider_event_id,
            )
        )
    ).scalar_one_or_none()
    if existing_revenue_event is not None:
        if (
            existing_revenue_event.tenant_id != tenant_id
            or existing_revenue_event.deal_id != deal.id
        ):
            raise ConflictError("Sales payment provider event is already bound to another deal")
        return tenant_id, str(deal.order_id) if deal.order_id else str(existing_revenue_event.order_id)

    event_ids = list(deal_metadata.get("sales_payment_event_ids") or [])
    if provider_event_id in event_ids:
        return tenant_id, str(deal.order_id) if deal.order_id else None

    amount_raw = data.get("amount_received") or data.get("amount") or 0
    try:
        amount_minor = int(amount_raw)
    except (TypeError, ValueError) as exc:
        raise ValidationAppError("Sales payment event amount must be numeric") from exc
    if amount_minor <= 0:
        raise ValidationAppError("Sales payment event must contain a positive paid amount")
    currency = str(data.get("currency") or deal.currency or "usd").upper()
    if provider == "zarinpal" and currency == "IRR":
        amount = Decimal(amount_minor)
    else:
        amount = _major_units(amount_minor, currency.lower())
    if currency != str(deal.currency or "").upper() or amount != Decimal(str(deal.amount)):
        raise ConflictError("Sales payment amount/currency does not match the governed deal commitment")

    order = None
    if deal.order_id:
        order = (
            await db.execute(
                select(BusinessOrder).where(
                    BusinessOrder.id == deal.order_id,
                    BusinessOrder.tenant_id == tenant_id,
                )
            )
        ).scalar_one_or_none()

    if order is None:
        order = BusinessOrder(
            tenant_id=tenant_id,
            number=f"AIW-{str(deal.id)[:8]}-{provider_event_id[:8]}",
            status="confirmed",
            currency=currency,
            customer_name=deal.customer_name,
            customer_email=deal.customer_email,
            order_date=datetime.now(timezone.utc).date(),
            subtotal=amount,
            tax_amount=Decimal("0"),
            total=amount,
            line_items=[{
                "description": deal.title,
                "quantity": 1,
                "unit_price": float(amount),
                "currency": currency,
            }],
            notes="Created from verified sales payment provider event.",
            metadata_={
                "source": "ai_workforce",
                "sales_deal_id": str(deal.id),
                "provider": provider,
                "provider_event_id": provider_event_id,
                "payment_object_id": data.get("id"),
            },
        )
        db.add(order)
        await db.flush()
        deal.order_id = order.id

    # Commercial ownership is downstream of the verified provider payment and
    # the tenant-scoped deal contract; order status alone never grants ownership.
    if (deal.metadata_ or {}).get("cosmetic_purchase"):
        from app.services.cosmetic_entitlement_service import grant_from_verified_payment
        await grant_from_verified_payment(
            db,
            tenant_id=tenant_id,
            deal=deal,
            source_order_id=order.id,
        )
    if (deal.metadata_ or {}).get("skill_purchase"):
        from app.services.skill_purchase_entitlement_service import grant_from_verified_payment
        await grant_from_verified_payment(
            db,
            tenant_id=tenant_id,
            deal=deal,
            source_order_id=order.id,
            provider=provider,
            provider_event_id=provider_event_id,
        )

    marketplace_purchase_id = None
    marketplace_seller_tenant_id = None
    if (deal.metadata_ or {}).get("skill_marketplace_purchase"):
        from app.services.skill_marketplace_purchase_service import SkillMarketplacePurchaseStatus
        from app.models.skill_marketplace_purchase import SkillMarketplacePurchase
        from app.services import skill_marketplace_service
        marketplace = (deal.metadata_ or {}).get("skill_marketplace_purchase") or {}
        try:
            marketplace_purchase_id = uuid.UUID(str(marketplace.get("purchase_id"))) if marketplace.get("purchase_id") else None
            marketplace_publication_id = uuid.UUID(str(marketplace["publication_id"]))
        except (TypeError, ValueError, KeyError) as exc:
            raise ValidationAppError("skill marketplace payment metadata is malformed") from exc
        if marketplace_purchase_id is None:
            raise ValidationAppError("skill marketplace payment metadata is missing purchase_id")
        purchase = (
            await db.execute(
                select(SkillMarketplacePurchase).where(
                    SkillMarketplacePurchase.id == marketplace_purchase_id,
                    SkillMarketplacePurchase.buyer_tenant_id == tenant_id,
                    SkillMarketplacePurchase.business_deal_id == deal.id,
                ).with_for_update()
            )
        ).scalar_one_or_none()
        if purchase is None:
            raise NotFoundError("skill marketplace purchase record not found")
        if purchase.status == SkillMarketplacePurchaseStatus.PAID:
            return tenant_id, str(order.id)
        marketplace_seller_tenant_id = purchase.seller_tenant_id
        await skill_marketplace_service.install(
            db,
            tenant_id=tenant_id,
            employee_id=purchase.employee_id,
            skill_package_id=purchase.skill_package_id,
            source_publication_id=marketplace_publication_id,
            actor_id=None,
        )
        purchase.status = SkillMarketplacePurchaseStatus.PAID
        purchase.provider = provider
        purchase.provider_event_id = provider_event_id
        purchase.metadata_ = {
            **(purchase.metadata_ or {}),
            "provider_payment_verified": True,
            "source_order_id": str(order.id),
        }
        await db.flush()

    # Entitlement settlement updates the governed deal metadata; reload it
    # before adding payment markers so those ownership markers are preserved.
    deal_metadata = dict(deal.metadata_ or {})
    event_ids = list(deal_metadata.get("sales_payment_event_ids") or [])
    event_ids.append(provider_event_id)
    deal_metadata["sales_payment_event_ids"] = event_ids[-20:]
    deal_metadata["payment_verified"] = True

    revenue_event = (
        await db.execute(
            select(WorkforceRevenueEvent).where(
                WorkforceRevenueEvent.provider == provider,
                WorkforceRevenueEvent.provider_event_id == provider_event_id,
            )
        )
    ).scalar_one_or_none()
    if revenue_event is None:
        revenue_event = WorkforceRevenueEvent(
            tenant_id=tenant_id,
            deal_id=deal.id,
            order_id=order.id,
            provider=provider,
            provider_event_id=provider_event_id,
            amount=amount,
            currency=currency,
            verified_at=datetime.now(timezone.utc),
            source=f"{provider}_verified_sales_payment",
            metadata_={
                "payment_object_id": data.get("id"),
                "sales_deal_id": str(deal.id),
                "business_order_id": str(order.id),
                **(
                    {
                        "skill_marketplace_purchase_id": str(marketplace_purchase_id),
                        "skill_marketplace_seller_tenant_id": str(marketplace_seller_tenant_id),
                        "source": "skill_marketplace",
                    }
                    if marketplace_purchase_id is not None
                    else {}
                ),
            },
        )
        db.add(revenue_event)
    deal_metadata["payment_provider"] = provider
    deal_metadata["payment_provider_event_id"] = provider_event_id
    deal_metadata["payment_amount"] = float(amount)
    deal_metadata["payment_currency"] = currency
    deal.metadata_ = deal_metadata
    deal.stage = "won"
    deal.probability = 100
    try:
        await db.flush()
    except IntegrityError as exc:
        # The provider-event uniqueness constraint is the final concurrency
        # guard. Fail closed rather than allowing a concurrent cross-deal
        # replay to look like a successful settlement.
        raise ConflictError("Sales payment provider event was concurrently bound to another deal") from exc
    return tenant_id, str(order.id)


async def apply_webhook_event(db: AsyncSession, event) -> dict:
    """Translate verified Stripe events into provider-neutral billing state.

    Stripe does not guarantee webhook delivery order. Subscription state is
    therefore serialized on the Subscription row and older lifecycle events
    are recorded but are not allowed to regress newer provider state.
    """
    provider_event_id = event["id"]
    existing = (
        await db.execute(
            select(BillingEvent).where(
                BillingEvent.provider == "stripe",
                BillingEvent.provider_event_id == provider_event_id,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return {
            "event_id": str(existing.id),
            "stripe_event_id": provider_event_id,
            "event_type": existing.event_type,
            "duplicate": True,
        }

    event_type = event["type"]
    data = event["data"]["object"]
    event_created_at = int(event.get("created") or 0)

    tenant_id: uuid.UUID | None = None
    plan_code: str | None = None
    status: str | None = None
    stale = False

    if event_type == "payment_intent.succeeded":
        tenant_id, order_id = await apply_verified_sales_payment(
            db,
            provider="stripe",
            provider_event_id=provider_event_id,
            data=data,
        )
        status = "paid"
        plan_code = None
    elif event_type == "checkout.session.completed" and (data.get("metadata") or {}).get("sales_deal_id"):
        if data.get("payment_status") != "paid":
            raise ValidationAppError("Sales checkout completion is not a verified paid event")
        tenant_id, order_id = await apply_verified_sales_payment(
            db,
            provider="stripe",
            provider_event_id=provider_event_id,
            data={
                **data,
                "amount_received": data.get("amount_total"),
            },
        )
        status = "paid"
        plan_code = None
    elif event_type == "checkout.session.completed":
        tenant_ref = data.get("client_reference_id") or (data.get("metadata") or {}).get("tenant_id")
        if tenant_ref:
            tenant_id = uuid.UUID(tenant_ref)
        plan_code = (data.get("metadata") or {}).get("plan_code")
        status = "active"
        if tenant_id is not None:
            sub = await billing_service.ensure_subscription(db, tenant_id=tenant_id)
            sub, stale = await _lock_subscription_for_lifecycle(
                db, subscription_id=sub.id, event_created_at=event_created_at
            )
            if not stale:
                sub.provider = "stripe"
                if data.get("customer"):
                    sub.provider_customer_id = data["customer"]
                if data.get("subscription"):
                    sub.provider_subscription_id = data["subscription"]
                sub.trial_ends_at = None
                await db.flush()

    elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
        stripe_sub_id = data.get("id")
        tenant_ref = (data.get("metadata") or {}).get("tenant_id")
        if tenant_ref:
            tenant_id = uuid.UUID(tenant_ref)
        else:
            existing = (
                await db.execute(select(Subscription).where(Subscription.provider_subscription_id == stripe_sub_id))
            ).scalar_one_or_none()
            tenant_id = existing.tenant_id if existing else None

        stripe_status = data.get("status")
        status = {"active": "active", "trialing": "trialing", "past_due": "past_due", "canceled": "canceled", "unpaid": "past_due"}.get(
            stripe_status, None
        )
        items = (data.get("items") or {}).get("data") or []
        if items:
            price_id = (items[0].get("price") or {}).get("id")
            if price_id:
                plan_code = _plan_code_for_price_id(price_id)
        if tenant_id is not None:
            sub = await billing_service.ensure_subscription(db, tenant_id=tenant_id)
            sub, stale = await _lock_subscription_for_lifecycle(
                db, subscription_id=sub.id, event_created_at=event_created_at
            )
            if not stale:
                sub.provider = "stripe"
                sub.provider_subscription_id = stripe_sub_id
                if data.get("customer"):
                    sub.provider_customer_id = data["customer"]
                period_start = data.get("current_period_start")
                period_end = data.get("current_period_end")
                if period_start:
                    sub.current_period_start = datetime.fromtimestamp(period_start, tz=timezone.utc)
                if period_end:
                    sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)
                trial_end = data.get("trial_end")
                sub.trial_ends_at = datetime.fromtimestamp(trial_end, tz=timezone.utc) if trial_end else None
                await db.flush()

    elif event_type == "customer.subscription.deleted":
        stripe_sub_id = data.get("id")
        existing = (
            await db.execute(select(Subscription).where(Subscription.provider_subscription_id == stripe_sub_id))
        ).scalar_one_or_none()
        if existing is not None:
            tenant_id = existing.tenant_id
            status = "canceled"
            _, stale = await _lock_subscription_for_lifecycle(
                db, subscription_id=existing.id, event_created_at=event_created_at
            )

    elif event_type == "invoice.payment_failed":
        stripe_sub_id = data.get("subscription")
        existing = (
            await db.execute(select(Subscription).where(Subscription.provider_subscription_id == stripe_sub_id))
        ).scalar_one_or_none()
        if existing is not None:
            tenant_id = existing.tenant_id
            status = "past_due"
            _, stale = await _lock_subscription_for_lifecycle(
                db, subscription_id=existing.id, event_created_at=event_created_at
            )

    elif event_type in {"refund.created", "refund.updated", "charge.refunded"}:
        from app.services.refund_service import reconcile_stripe_refund_event
        row = await reconcile_stripe_refund_event(db, event=event)
        tenant_id = row.tenant_id if row is not None else None
        status = row.status if row is not None else None

    else:
        logger.info("stripe_webhook_ignored_event_type", extra={"event_type": event_type})

    billing_event = await billing_service.record_event(
        db,
        tenant_id=tenant_id,
        provider="stripe",
        provider_event_id=provider_event_id,
        event_type=event_type,
        payload={
            "id": data.get("id"),
            "object": data.get("object"),
            "stripe_event_created_at": event_created_at or None,
            "stale_lifecycle_event": stale,
        },
        plan_code=None if stale else plan_code,
        status=None if stale else status,
    )
    return {"event_id": str(billing_event.id), "stripe_event_id": provider_event_id, "event_type": event_type, "duplicate": False, "stale": stale}