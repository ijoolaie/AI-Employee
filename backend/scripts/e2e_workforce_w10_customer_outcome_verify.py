"""W10 customer outcome / verified revenue-event real-stack evidence."""
from __future__ import annotations
import asyncio, os, sys, uuid
from datetime import datetime, timezone
from decimal import Decimal
PROJECT_ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
if PROJECT_ROOT not in sys.path: sys.path.insert(0,PROJECT_ROOT)

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.business_deal import BusinessDeal
from app.models.business_order import BusinessOrder
from app.models.workforce_revenue_event import WorkforceRevenueEvent
from app.services import edition_service, license_service
from app.modules.employees.sales.service import create_deal
from app.services.stripe_service import apply_verified_sales_payment

async def main():
    suffix=f"{os.environ.get('GITHUB_RUN_ID','local')}-{uuid.uuid4().hex[:8]}"
    async with AsyncSessionLocal() as db:
        vendor=Tenant(name=f"W10 Outcome Vendor {suffix}",slug=f"w10-outcome-vendor-{suffix}",status="active",tenant_kind=edition_service.EDITION_VENDOR)
        db.add(vendor); await db.flush()
        reseller=Tenant(name=f"W10 Outcome Reseller {suffix}",slug=f"w10-outcome-reseller-{suffix}",status="active",tenant_kind=edition_service.EDITION_RESELLER,parent_tenant_id=vendor.id)
        db.add(reseller); await db.flush()
        customer=Tenant(name=f"W10 Outcome Customer {suffix}",slug=f"w10-outcome-customer-{suffix}",status="active",tenant_kind=edition_service.EDITION_CUSTOMER,parent_tenant_id=reseller.id)
        db.add(customer); await db.flush()
        actor=User(tenant_id=customer.id,email=f"w10-outcome-{suffix}@example.invalid",password_hash="fixture",full_name="W10 Outcome Owner",is_active=True)
        db.add(actor); await db.flush()
        await license_service.issue_license(db,issuer=reseller,tenant=customer,feature_codes=["employee.run"],metadata={"certification_fixture":True,"purpose":"W10-customer-outcome"})
        
        deal=await create_deal(
            db,tenant_id=customer.id,actor_id=actor.id,
            title="Governed AI Workforce pilot",
            customer_name="Verified Fixture Customer",
            customer_email="customer@example.invalid",
            amount=12500,currency="USD",stage="proposal",probability=50,
            source="w10-dogfood",
        )
        deal_id=deal.id
        await db.commit()

        provider_event_id=f"w10-contract-payment-{uuid.uuid4().hex}"
        event={
            "id":provider_event_id,
            "metadata":{"tenant_id":str(customer.id),"sales_deal_id":str(deal_id)},
            "amount_received":1250000,
            "currency":"USD",
            "id":f"payment-{uuid.uuid4().hex}",
        }
        async with AsyncSessionLocal() as settle_db:
            tenant_id,order_id=await apply_verified_sales_payment(
                settle_db,provider="contract-test",provider_event_id=provider_event_id,data=event
            )
            await settle_db.commit()
            settled=(await settle_db.execute(select(BusinessDeal).where(BusinessDeal.id==deal_id, BusinessDeal.tenant_id==customer.id))).scalar_one()
            order=(await settle_db.execute(select(BusinessOrder).where(BusinessOrder.id==uuid.UUID(str(order_id)),BusinessOrder.tenant_id==customer.id))).scalar_one()
            revenue=(await settle_db.execute(select(WorkforceRevenueEvent).where(WorkforceRevenueEvent.provider=="contract-test",WorkforceRevenueEvent.provider_event_id==provider_event_id))).scalar_one()
            assert settled.stage=="won" and settled.probability==100
            assert settled.metadata_.get("payment_verified") is True
            assert order.status=="confirmed" and order.total==Decimal("12500")
            assert revenue.tenant_id==customer.id and revenue.deal_id==deal_id
            assert revenue.amount==Decimal("12500") and revenue.currency=="USD"

        async with AsyncSessionLocal() as replay_db:
            tenant_id2,order_id2=await apply_verified_sales_payment(
                replay_db,provider="contract-test",provider_event_id=provider_event_id,data=event
            )
            await replay_db.commit()
            count=(await replay_db.execute(select(WorkforceRevenueEvent).where(WorkforceRevenueEvent.provider=="contract-test",WorkforceRevenueEvent.provider_event_id==provider_event_id))).scalars().all()
            assert tenant_id2==customer.id and str(order_id2)==str(order_id) and len(count)==1

        print("W10 CUSTOMER IDENTITY + QUALIFICATION FIXTURE PASS")
        print("W10 GOVERNED PROPOSAL/PILOT DEAL PASS stage=proposal")
        print("W10 VERIFIED PAYMENT CORRELATION PASS")
        print("W10 REVENUE LEDGER SETTLEMENT PASS")
        print("W10 PAYMENT REPLAY IDEMPOTENCY PASS")
        print("W10 ORDER SETTLEMENT PASS")
        print("W10 REAL CUSTOMER/REAL REVENUE OUTCOME NOT_VERIFIED provider=contract-test")

if __name__=="__main__":
    try: asyncio.run(main())
    except Exception as exc:
        print(f"W10 CUSTOMER OUTCOME REAL-STACK E2E FAIL: {exc}",file=sys.stderr); raise SystemExit(1)
