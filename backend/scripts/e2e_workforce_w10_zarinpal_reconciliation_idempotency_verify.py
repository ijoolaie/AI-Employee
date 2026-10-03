"""Real-stack synthetic ZarinPal revenue reconciliation/idempotency certification for W10.

This never contacts ZarinPal. It feeds an already-verified ZarinPal-shaped
payment into the provider-neutral reconciliation boundary and verifies that
replaying the same provider reference cannot create a second revenue ledger
row or business order.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from decimal import Decimal

from sqlalchemy import select

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import AsyncSessionLocal
from app.models.business_deal import BusinessDeal
from app.models.business_order import BusinessOrder
from app.models.workforce_revenue_event import WorkforceRevenueEvent
from app.core.exceptions import ConflictError
from app.services.stripe_service import apply_verified_sales_payment
from scripts.e2e_workforce_w10_dogfood_verify import prepare


async def main() -> None:
    os.environ.pop("SALES_INBOUND_TENANT_ID", None)
    tenant_id, _instance_id, _runs, owner_id, _reviewer_id, _ = await prepare()

    deal_id = uuid.uuid4()
    reference_id = f"w10-zarinpal-ref-{uuid.uuid4().hex}"

    async with AsyncSessionLocal() as db:
        db.add(
            BusinessDeal(
                id=deal_id,
                tenant_id=tenant_id,
                title="W10 synthetic ZarinPal revenue idempotency certification",
                customer_name="Synthetic ZarinPal Prospect",
                customer_email="synthetic-zarinpal@example.invalid",
                amount=Decimal("100000"),
                currency="IRR",
                stage="proposal",
                probability=50,
                source="ai_workforce_zarinpal_reconciliation_idempotency_test",
                notes="Synthetic provider event only; no ZarinPal network call.",
                metadata_={},
                created_by=owner_id,
            )
        )
        await db.commit()

    event_data = {
        "id": reference_id,
        "amount_received": 100000,
        "currency": "IRR",
        "metadata": {
            "tenant_id": str(tenant_id),
            "sales_deal_id": str(deal_id),
        },
    }

    async with AsyncSessionLocal() as db:
        tenant_first, order_first = await apply_verified_sales_payment(
            db,
            provider="zarinpal",
            provider_event_id=reference_id,
            data=event_data,
        )
        await db.commit()

        assert str(tenant_first) == str(tenant_id)
        assert order_first

        revenue = (
            await db.execute(
                select(WorkforceRevenueEvent).where(
                    WorkforceRevenueEvent.provider == "zarinpal",
                    WorkforceRevenueEvent.provider_event_id == reference_id,
                )
            )
        ).scalar_one()
        assert revenue.tenant_id == tenant_id
        assert revenue.deal_id == deal_id
        assert revenue.amount == Decimal("100000")
        assert revenue.currency == "IRR"
        assert revenue.source == "zarinpal_verified_sales_payment"
        assert revenue.verified_at is not None
        assert revenue.verified_at.tzinfo is not None

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
        assert order_row.total == Decimal("100000")

        tenant_second, order_second = await apply_verified_sales_payment(
            db,
            provider="zarinpal",
            provider_event_id=reference_id,
            data=event_data,
        )
        await db.commit()

        assert str(tenant_second) == str(tenant_id)
        assert order_second == order_first

        revenue_rows = (
            await db.execute(
                select(WorkforceRevenueEvent).where(
                    WorkforceRevenueEvent.provider == "zarinpal",
                    WorkforceRevenueEvent.provider_event_id == reference_id,
                )
            )
        ).scalars().all()
        order_rows = (
            await db.execute(
                select(BusinessOrder).where(
                    BusinessOrder.id == deal_row.order_id,
                    BusinessOrder.tenant_id == tenant_id,
                )
            )
        ).scalars().all()

        assert len(revenue_rows) == 1
        assert len(order_rows) == 1

        cross_deal_id = uuid.uuid4()
        db.add(
            BusinessDeal(
                id=cross_deal_id,
                tenant_id=tenant_id,
                title="W10 synthetic ZarinPal cross-deal replay guard",
                customer_name="Synthetic Replay Prospect",
                customer_email="synthetic-replay@example.invalid",
                amount=Decimal("100000"),
                currency="IRR",
                stage="proposal",
                probability=50,
                source="ai_workforce_zarinpal_cross_deal_replay_test",
                notes="Synthetic provider event replay must not settle another deal.",
                metadata_={},
                created_by=owner_id,
            )
        )
        await db.commit()

        cross_deal_event = {
            **event_data,
            "metadata": {
                "tenant_id": str(tenant_id),
                "sales_deal_id": str(cross_deal_id),
            },
        }
        try:
            await apply_verified_sales_payment(
                db,
                provider="zarinpal",
                provider_event_id=reference_id,
                data=cross_deal_event,
            )
        except ConflictError as exc:
            assert "already bound to another deal" in str(exc)
            await db.rollback()
        else:
            raise AssertionError("cross-deal provider reference replay must be rejected")

        cross_deal_row = (
            await db.execute(
                select(BusinessDeal).where(
                    BusinessDeal.id == cross_deal_id,
                    BusinessDeal.tenant_id == tenant_id,
                )
            )
        ).scalar_one()
        assert cross_deal_row.stage == "proposal"
        assert cross_deal_row.order_id is None

    print("W10 ZARINPAL CROSS-DEAL REPLAY GUARD PASS same_reference_rejected=1 second_deal_unsettled=1")
    print("W10 SYNTHETIC ZARINPAL RECONCILIATION PASS")
    print("W10 WORKFORCE REVENUE EVENT PASS provider=zarinpal amount=100000 IRR")
    print("W10 ZARINPAL REVENUE IDEMPOTENCY PASS duplicate_reference=1 ledger_rows=1 order_rows=1")
    print("W10 REAL ZARINPAL NETWORK PAYMENT NOT_RUN")


if __name__ == "__main__":
    asyncio.run(main())
