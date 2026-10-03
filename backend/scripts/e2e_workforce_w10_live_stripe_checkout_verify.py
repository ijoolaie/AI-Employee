"""Live Stripe Checkout creation certification for W10.

This workflow creates a real Stripe Checkout Session for a tiny certification
deal. It never confirms payment, creates a PaymentIntent directly, or calls a
customer payment endpoint. Revenue remains NOT_VERIFIED until Stripe delivers
and the application independently reconciles a real successful payment event.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from decimal import Decimal

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import AsyncSessionLocal
from app.models.business_deal import BusinessDeal
from app.models.tenant import Tenant
from app.services.workforce_sales_payment_provider import create_sales_checkout_session
from scripts.e2e_workforce_w10_dogfood_verify import prepare


async def main() -> None:
    if not os.environ.get("STRIPE_SECRET_KEY"):
        raise RuntimeError("STRIPE_SECRET_KEY is required for live checkout certification")

    tenant_id, _instance_id, _runs, owner_id, _reviewer_id, _ = await prepare()
    deal_id = uuid.uuid4()
    idempotency_key = f"w10-live-stripe-checkout-{uuid.uuid4().hex}"
    customer_email = os.environ.get(
        "W10_STRIPE_CERTIFICATION_EMAIL",
        "stripe-certification@example.invalid",
    ).strip()

    async with AsyncSessionLocal() as db:
        deal = BusinessDeal(
            id=deal_id,
            tenant_id=tenant_id,
            title="W10 live Stripe checkout certification",
            customer_name="Stripe Certification Prospect",
            customer_email=customer_email,
            amount=Decimal("1.00"),
            currency="USD",
            stage="proposal",
            probability=50,
            source="ai_workforce_live_stripe_checkout_certification",
            notes="Certification fixture. Creating checkout only; payment must be manual.",
            created_by=owner_id,
        )
        db.add(deal)
        await db.commit()

    result = await create_sales_checkout_session(
        tenant_id=tenant_id,
        deal_id=deal_id,
        amount=Decimal("1.00"),
        currency="USD",
        customer_email=customer_email,
        idempotency_key=idempotency_key,
    )

    assert result.provider == "stripe"
    assert result.provider_execution == "accepted"
    assert result.executed is True
    assert result.checkout_url and result.checkout_url.startswith("https://checkout.stripe.com/")
    assert result.provider_payment_id is not None

    print("W10 LIVE STRIPE CHECKOUT PASS")
    print(f"W10 LIVE STRIPE CHECKOUT SESSION={result.provider_payment_id}")
    print(f"W10 LIVE STRIPE DEAL_ID={deal_id}")
    print(f"W10 LIVE STRIPE CHECKOUT_URL={result.checkout_url}")
    print("W10 LIVE STRIPE PAYMENT NOT_RUN: checkout created, no payment confirmation was attempted")
    print("W10 REVENUE OUTCOME NOT_VERIFIED: awaiting an independently verified real Stripe payment webhook")


if __name__ == "__main__":
    asyncio.run(main())
