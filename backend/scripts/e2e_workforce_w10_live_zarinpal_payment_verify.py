"""Live ZarinPal payment certification for W10.

Manual-only external payment flow:
1. Create a real ZarinPal payment request.
2. Print the gateway URL.
3. Wait for the operator/customer to complete payment manually.
4. Verify the payment directly with ZarinPal.
5. Reconcile the verified result into WorkforceRevenueEvent.

The workflow never submits card credentials or attempts payment automatically.
Sandbox is the default; production mode must be explicitly confirmed.
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
from app.services import zarinpal_service
from app.services.stripe_service import apply_verified_sales_payment
from app.services.workforce_sales_payment_provider import create_sales_checkout_session
from scripts.e2e_workforce_w10_dogfood_verify import prepare


async def main() -> None:
    merchant_id = os.environ.get("ZARINPAL_MERCHANT_ID", "").strip()
    if not merchant_id:
        raise RuntimeError("ZARINPAL_MERCHANT_ID is required for live ZarinPal certification")

    sandbox = os.environ.get("ZARINPAL_SANDBOX", "true").strip().lower() in {"1", "true", "yes"}
    confirmation = os.environ.get("W10_ZARINPAL_EXTERNAL_PAYMENT_CONFIRMATION", "").strip()
    required = "I_UNDERSTAND_THIS_CREATES_A_REAL_ZARINPAL_CHECKOUT"
    if confirmation != required:
        raise RuntimeError(
            "External payment certification requires explicit confirmation: "
            f"{required}"
        )

    wait_minutes = int(os.environ.get("W10_ZARINPAL_WAIT_MINUTES", "20"))
    if wait_minutes < 1 or wait_minutes > 60:
        raise RuntimeError("W10_ZARINPAL_WAIT_MINUTES must be between 1 and 60")

    amount_irr = Decimal(os.environ.get("W10_ZARINPAL_AMOUNT_IRR", "100000"))
    if amount_irr < Decimal("10000"):
        raise RuntimeError("W10_ZARINPAL_AMOUNT_IRR must be at least 10000 IRR")

    tenant_id, _instance_id, _runs, owner_id, _reviewer_id, _ = await prepare()
    deal_id = uuid.uuid4()
    idempotency_key = f"w10-live-zarinpal-{uuid.uuid4().hex}"
    customer_email = os.environ.get(
        "W10_ZARINPAL_CERTIFICATION_EMAIL",
        "zarinpal-certification@example.invalid",
    ).strip()

    async with AsyncSessionLocal() as db:
        deal = BusinessDeal(
            id=deal_id,
            tenant_id=tenant_id,
            title="W10 live ZarinPal payment certification",
            customer_name="ZarinPal Certification Prospect",
            customer_email=customer_email,
            amount=amount_irr,
            currency="IRR",
            stage="proposal",
            probability=50,
            source="ai_workforce_live_zarinpal_payment_certification",
            notes="Certification fixture. Payment is manual and explicitly confirmed.",
            created_by=owner_id,
        )
        db.add(deal)
        await db.commit()

        result = await create_sales_checkout_session(
            tenant_id=tenant_id,
            deal_id=deal_id,
            amount=amount_irr,
            currency="IRR",
            customer_email=customer_email,
            idempotency_key=idempotency_key,
            db=db,
        )

    assert result.provider == "zarinpal"
    assert result.provider_execution == "accepted"
    assert result.executed is True
    assert result.checkout_url and result.checkout_url.startswith(("https://sandbox.zarinpal.com/", "https://www.zarinpal.com/"))
    assert result.provider_payment_id

    print("W10 LIVE ZARINPAL CHECKOUT PASS")
    print(f"W10 LIVE ZARINPAL MODE={'SANDBOX' if sandbox else 'LIVE'}")
    print(f"W10 LIVE ZARINPAL DEAL_ID={deal_id}")
    print(f"W10 LIVE ZARINPAL AUTHORITY={result.provider_payment_id}")
    print(f"W10 LIVE ZARINPAL CHECKOUT_URL={result.checkout_url}")
    print("W10 LIVE ZARINPAL PAYMENT ACTION: MANUAL ONLY")
    print("W10 LIVE ZARINPAL WAITING: complete the payment in the gateway; the runner will verify it.")

    deadline = asyncio.get_running_loop().time() + wait_minutes * 60
    verification = None
    while asyncio.get_running_loop().time() < deadline:
        try:
            verification = await zarinpal_service.verify_payment(
                authority=str(result.provider_payment_id),
                amount=amount_irr,
                currency="IRR",
            )
            print("W10 LIVE ZARINPAL VERIFY PASS")
            break
        except Exception as exc:
            print(f"W10 LIVE ZARINPAL PAYMENT PENDING: {type(exc).__name__}")
            await asyncio.sleep(15)

    if verification is None:
        raise RuntimeError("ZarinPal payment was not independently verified within the certification window")

    ref_id = verification.get("ref_id")
    if not ref_id:
        raise RuntimeError("ZarinPal verification returned no ref_id")

    async with AsyncSessionLocal() as db:
        tenant_id_verified, order_id = await apply_verified_sales_payment(
            db,
            provider="zarinpal",
            provider_event_id=str(ref_id),
            data={
                "id": str(ref_id),
                "amount_received": int(amount_irr),
                "currency": "IRR",
                "metadata": {
                    "tenant_id": str(tenant_id),
                    "sales_deal_id": str(deal_id),
                },
            },
        )
        await db.commit()

    assert str(tenant_id_verified) == str(tenant_id)
    print(f"W10 WORKFORCE REVENUE EVENT PASS provider=zarinpal amount={amount_irr} IRR")
    print(f"W10 ZARINPAL REFERENCE_ID={ref_id}")
    print(f"W10 ZARINPAL ORDER_ID={order_id}")
    print("W10 FIRST REVENUE OUTCOME VERIFIED: independently verified ZarinPal payment reconciled")


if __name__ == "__main__":
    asyncio.run(main())
