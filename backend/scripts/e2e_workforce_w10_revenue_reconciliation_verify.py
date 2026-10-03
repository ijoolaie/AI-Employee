"""Real-stack synthetic Stripe reconciliation certification for W10 revenue.

This never contacts Stripe. It feeds a provider-shaped, already-verified event
directly into the webhook reconciliation service, then verifies the independent
WorkforceRevenueEvent ledger, order/deal settlement, and duplicate idempotency.
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

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.business_deal import BusinessDeal
from app.models.business_order import BusinessOrder
from app.models.workforce_revenue_event import WorkforceRevenueEvent
from app.services import stripe_service
from scripts.e2e_workforce_w10_dogfood_verify import execute, prepare


async def main() -> None:
    os.environ.pop("SALES_INBOUND_TENANT_ID", None)
    tenant_id, instance_id, runs, owner_id, reviewer_id, _ = await prepare()

    deal_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        db.add(
            BusinessDeal(
                id=deal_id,
                tenant_id=tenant_id,
                title="W10 synthetic Stripe revenue certification",
                customer_name="Synthetic Revenue Prospect",
                customer_email="synthetic-revenue@example.invalid",
                amount=Decimal("100"),
                currency="USD",
                stage="proposal",
                probability=50,
                source="ai_workforce_revenue_reconciliation_test",
                notes="Synthetic provider event only; no Stripe network call.",
                metadata_={},
                created_by=owner_id,
            )
        )
        await db.commit()

    event_id = f"evt_w10_revenue_{uuid.uuid4().hex}"
    async with AsyncSessionLocal() as db:
        event = {
            "id": event_id,
            "type": "payment_intent.succeeded",
            "created": 1791013200,
            "data": {
                "object": {
                    "id": f"pi_w10_{uuid.uuid4().hex}",
                    "object": "payment_intent",
                    "amount_received": 10000,
                    "currency": "usd",
                    "metadata": {
                        "tenant_id": str(tenant_id),
                        "sales_deal_id": str(deal_id),
                    },
                }
            },
        }
        result = await stripe_service.apply_webhook_event(db, event)
        await db.commit()

        assert result["duplicate"] is False
        revenue = (
            await db.execute(
                select(WorkforceRevenueEvent).where(
                    WorkforceRevenueEvent.provider == "stripe",
                    WorkforceRevenueEvent.provider_event_id == event_id,
                )
            )
        ).scalar_one()
        assert revenue.tenant_id == tenant_id
        assert revenue.deal_id == deal_id
        assert revenue.amount == Decimal("100")
        assert revenue.currency == "USD"
        assert revenue.source == "stripe_verified_sales_payment"

        deal_row = (
            await db.execute(
                select(BusinessDeal).where(
                    BusinessDeal.id == deal_id,
                    BusinessDeal.tenant_id == tenant_id,
                )
            )
        ).scalar_one()
        order_row = (
            await db.execute(
                select(BusinessOrder).where(
                    BusinessOrder.id == deal_row.order_id,
                    BusinessOrder.tenant_id == tenant_id,
                )
            )
        ).scalar_one()
        assert deal_row.stage == "won"
        assert deal_row.probability == 100
        assert order_row.total == Decimal("100")

        duplicate = await stripe_service.apply_webhook_event(db, event)
        assert duplicate["duplicate"] is True
        await db.commit()

        count = (
            await db.execute(
                select(WorkforceRevenueEvent).where(
                    WorkforceRevenueEvent.provider == "stripe",
                    WorkforceRevenueEvent.provider_event_id == event_id,
                )
            )
        )
        assert len(count.scalars().all()) == 1

    print("W10 SYNTHETIC STRIPE RECONCILIATION PASS")
    print("W10 WORKFORCE REVENUE EVENT PASS provider=stripe amount=100 USD")
    print("W10 REVENUE IDEMPOTENCY PASS duplicate_event=1 ledger_rows=1")
    print("W10 REAL STRIPE NETWORK PAYMENT NOT_RUN")


if __name__ == "__main__":
    asyncio.run(main())