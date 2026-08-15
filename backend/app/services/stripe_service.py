"""Stripe payment-provider adapter (Phase 6 — closing the Phase 4 commercial exit gate).

`app/services/billing_service.py` is deliberately provider-neutral (see its
module docstring): quota enforcement, MRR reporting, and the Subscription/
BillingEvent models know nothing about Stripe. This module is the adapter
that connects real Stripe Checkout/Billing-Portal/webhooks to that
provider-neutral core, without changing any of it.

Everything here fails closed when Stripe is not configured
(`settings.stripe_enabled` — both a secret key and a webhook secret must be
set) rather than silently no-op'ing, so a misconfigured deployment cannot
accidentally look like it has working payments.

IMPORTANT — what this module does NOT prove by itself: this code was
written and unit-tested (signature verification, event-type dispatch, plan
mapping) against the Stripe SDK's own request/response shapes, but this
delivery environment's network egress does not include api.stripe.com —
see documents/64_PHASE_6... for the exact verification boundary. A real
Checkout Session must be completed with real (or Stripe test-mode) keys,
in an environment that can actually reach Stripe, before the Phase 4
commercial exit gate can be considered closed.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.billing import BillingPlan, Subscription
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
    db: AsyncSession, stripe, *, tenant_id: uuid.UUID, sub: Subscription, user_email: str | None
) -> str:
    if sub.provider_customer_id:
        return sub.provider_customer_id

    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    customer = stripe.Customer.create(
        email=user_email,
        name=tenant.name if tenant else None,
        metadata={"tenant_id": str(tenant_id)},
    )
    sub.provider_customer_id = customer.id
    await db.flush()
    return customer.id


async def create_checkout_session(
    db: AsyncSession, *, tenant_id: uuid.UUID, user_id: uuid.UUID, plan_code: str
) -> str:
    """Creates a real Stripe Checkout Session (subscription mode) for the
    given plan and returns the URL the frontend should redirect the user
    to. Raises StripeNotConfiguredError if Stripe isn't set up, and
    ValidationAppError if the plan has no mapped Stripe Price ID (e.g. the
    free `starter` plan, which is not expected to go through Checkout)."""
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
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    customer_id = await _get_or_create_stripe_customer(
        db, stripe, tenant_id=tenant_id, sub=sub, user_email=user.email if user else None
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
    )
    return session.url


async def create_portal_session(db: AsyncSession, *, tenant_id: uuid.UUID) -> str:
    """Creates a real Stripe Billing Portal session so the tenant can
    self-serve upgrade/downgrade/cancel/update payment method — this is
    what makes the "clear upgrade path" requirement (03_Roadmap_v1.1 §9)
    real rather than an internal-only API call."""
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
    """Verifies the Stripe-Signature header against STRIPE_WEBHOOK_SECRET
    using Stripe's own SDK (HMAC-SHA256 + timestamp tolerance — Stripe's
    verification, not a reimplementation of it), and returns the parsed
    Event object. Raises on any signature/timestamp failure — this is the
    only path by which billing_service state can be changed by an
    unauthenticated caller, so it fails closed."""
    stripe = _client()
    settings = get_settings()
    try:
        return stripe.Webhook.construct_event(raw_body, sig_header, settings.stripe_webhook_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise ValidationAppError("Invalid Stripe webhook signature or payload") from exc


async def apply_webhook_event(db: AsyncSession, event) -> dict:
    """Translates a verified Stripe Event into the provider-neutral
    billing_service calls. Idempotent: billing_service.record_event
    de-duplicates on (provider, provider_event_id), so Stripe's
    at-least-once delivery is safe to replay."""
    event_type = event["type"]
    data = event["data"]["object"]

    tenant_id: uuid.UUID | None = None
    plan_code: str | None = None
    status: str | None = None

    if event_type == "checkout.session.completed":
        tenant_ref = data.get("client_reference_id") or (data.get("metadata") or {}).get("tenant_id")
        if tenant_ref:
            tenant_id = uuid.UUID(tenant_ref)
        plan_code = (data.get("metadata") or {}).get("plan_code")
        status = "active"
        if tenant_id is not None:
            sub = await billing_service.ensure_subscription(db, tenant_id=tenant_id)
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

    elif event_type == "invoice.payment_failed":
        stripe_sub_id = data.get("subscription")
        existing = (
            await db.execute(select(Subscription).where(Subscription.provider_subscription_id == stripe_sub_id))
        ).scalar_one_or_none()
        if existing is not None:
            tenant_id = existing.tenant_id
            status = "past_due"

    else:
        logger.info("stripe_webhook_ignored_event_type", extra={"event_type": event_type})

    billing_event = await billing_service.record_event(
        db,
        tenant_id=tenant_id,
        provider="stripe",
        provider_event_id=event["id"],
        event_type=event_type,
        payload={"id": data.get("id"), "object": data.get("object")},
        plan_code=plan_code,
        status=status,
    )
    return {"event_id": str(billing_event.id), "stripe_event_id": event["id"], "event_type": event_type}
