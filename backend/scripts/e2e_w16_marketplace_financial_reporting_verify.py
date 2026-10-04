"""Real PostgreSQL verification for read-only marketplace financial reporting."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.business_deal import BusinessDeal
from app.models.employee import Employee
from app.models.product import Product
from app.models.skill_marketplace_publication import SkillMarketplacePublication
from app.models.skill_marketplace_purchase import SkillMarketplacePurchase, SkillMarketplacePurchaseStatus
from app.models.skill_marketplace_settlement import SkillMarketplacePayoutStatus, SkillMarketplaceSettlement, SkillMarketplaceSettlementStatus
from app.models.skill_package import SkillPackage, SkillPackageStatus
from app.models.tenant import Tenant
from app.models.user import User
from app.models.workforce_revenue_event import WorkforceRevenueEvent
from app.services import edition_lifecycle_service, skill_marketplace_payout_destination, skill_marketplace_payout_service, skill_marketplace_reporting_service


async def verify() -> None:
    suffix = str(time.time_ns())[-12:]
    vendor_slug = f"w16-report-vendor-{suffix}"
    seller_a_slug = f"w16-report-seller-a-{suffix}"
    seller_b_slug = f"w16-report-seller-b-{suffix}"
    buyer_slug = f"w16-report-buyer-{suffix}"

    async with AsyncSessionLocal() as db:
        vendor = Tenant(name="W16 Reporting Vendor", slug=vendor_slug, tenant_kind="vendor")
        seller_a = Tenant(name="W16 Reporting Seller A", slug=seller_a_slug)
        seller_b = Tenant(name="W16 Reporting Seller B", slug=seller_b_slug)
        buyer = Tenant(name="W16 Reporting Buyer", slug=buyer_slug)
        db.add_all([vendor, seller_a, seller_b, buyer])
        await db.flush()

        admin = User(
            tenant_id=vendor.id,
            email=f"w16-report-admin-{suffix}@example.test",
            password_hash="certification-fixture",
            full_name="W16 Reporting Admin",
            is_active=True,
            is_platform_admin=True,
        )
        seller_actor = User(
            tenant_id=seller_a.id,
            email=f"w16-report-seller-{suffix}@example.test",
            password_hash="certification-fixture",
            full_name="W16 Reporting Seller Actor",
            is_active=True,
        )
        employee = Employee(
            tenant_id=buyer.id,
            slug=f"w16-report-employee-{suffix}",
            name="W16 Reporting Employee",
            kind="custom",
            is_active=True,
        )
        db.add_all([admin, seller_actor, employee])
        await db.flush()

        product = Product(
            tenant_id=seller_a.id,
            sku=f"w16-report-product-{suffix}",
            name="W16 Reporting Skill",
            category="employee_skill",
            price=20,
            currency="EUR",
            inventory=1,
            attributes={"skill_package_slug": f"w16-report-skill-{suffix}", "skill_package_version": 1},
            is_active=True,
        )
        db.add(product)
        await db.flush()

        package = SkillPackage(
            tenant_id=seller_a.id,
            product_id=product.id,
            slug=product.attributes["skill_package_slug"],
            name="W16 Reporting Skill",
            version=1,
            manifest={},
            compatibility={},
            presentation_metadata={},
            status=SkillPackageStatus.PUBLISHED,
        )
        db.add(package)
        await db.flush()

        publication = SkillMarketplacePublication(
            owner_tenant_id=seller_a.id,
            skill_package_id=package.id,
            visibility="public",
            title="W16 Reporting Skill",
            summary="reporting fixture",
            published_by=admin.id,
        )
        db.add(publication)
        await db.flush()

        deal = BusinessDeal(
            tenant_id=buyer.id,
            title="W16 Reporting Purchase",
            customer_name=employee.name,
            stage="won",
            amount=20,
            currency="EUR",
            probability=100,
            source="skill_marketplace",
        )
        db.add(deal)
        await db.flush()

        purchase = SkillMarketplacePurchase(
            buyer_tenant_id=buyer.id,
            seller_tenant_id=seller_a.id,
            publication_id=publication.id,
            employee_id=employee.id,
            skill_package_id=package.id,
            product_id=product.id,
            business_deal_id=deal.id,
            idempotency_key=f"w16-report-purchase-{suffix}",
            provider="contract-test",
            provider_event_id=f"evt-w16-report-{suffix}",
            status=SkillMarketplacePurchaseStatus.PAID,
            amount=Decimal("20.00"),
            currency="EUR",
        )
        revenue = WorkforceRevenueEvent(
            tenant_id=buyer.id,
            deal_id=deal.id,
            provider="contract-test",
            provider_event_id=f"evt-w16-report-revenue-{suffix}",
            amount=Decimal("20.00"),
            currency="EUR",
            verified_at=datetime.now(timezone.utc),
            source="skill_marketplace",
        )
        db.add_all([purchase, revenue])
        await db.flush()

        settlement = SkillMarketplaceSettlement(
            purchase_id=purchase.id,
            revenue_event_id=revenue.id,
            buyer_tenant_id=buyer.id,
            seller_tenant_id=seller_a.id,
            provider=revenue.provider,
            provider_event_id=revenue.provider_event_id,
            gross_amount=Decimal("20.00"),
            platform_fee_bps=1500,
            platform_fee_amount=Decimal("3.00"),
            seller_net_amount=Decimal("17.00"),
            currency="EUR",
            status=SkillMarketplaceSettlementStatus.RECORDED,
            payout_status=SkillMarketplacePayoutStatus.NOT_EXECUTED,
            metadata_={"source": "skill_marketplace"},
            verified_at=revenue.verified_at,
        )
        db.add(settlement)
        await db.flush()

        destination = await skill_marketplace_payout_destination.bind_payout_destination(
            db,
            seller_tenant_id=seller_a.id,
            provider="contract-test",
            destination_ref=f"seller-destination-{suffix}",
            actor_user_id=seller_actor.id,
        )
        await db.flush()
        assert destination.seller_tenant_id == seller_a.id
        assert destination.status.value == "active"

        proposal = await skill_marketplace_payout_service.create_payout_proposal(
            db,
            settlement_id=settlement.id,
            platform_admin_tenant_id=vendor.id,
            created_by_user_id=admin.id,
        )
        await db.flush()

        assert proposal.destination_id == destination.id
        assert proposal.destination_provider == "contract-test"
        assert proposal.destination_ref == destination.destination_ref

        summary = await skill_marketplace_reporting_service.marketplace_financial_summary(
            db,
            platform_admin_tenant_id=vendor.id,
        )
        assert summary["verified_settlement_count"] == 1
        assert summary["verified_paid_purchase_count"] == 1
        assert summary["payout_proposal_count"] == 1
        assert summary["by_currency"]["EUR"]["gross_amount"] == "20.00"
        assert summary["by_currency"]["EUR"]["platform_fee_amount"] == "3.00"
        assert summary["by_currency"]["EUR"]["seller_net_amount"] == "17.00"
        assert summary["external_customer_revenue_verified"] is False
        assert summary["external_seller_payout_verified"] is False
        assert proposal.execution_status.value == "not_executed"
        print("MARKETPLACE VERIFIED FINANCIAL SUMMARY PASS")

        seller_summary = await skill_marketplace_reporting_service.marketplace_financial_summary(
            db,
            platform_admin_tenant_id=vendor.id,
            seller_tenant_id=seller_a.id,
        )
        assert seller_summary["verified_settlement_count"] == 1
        assert seller_summary["payout_proposal_count"] == 1
        assert seller_summary["by_currency"]["EUR"]["seller_net_amount"] == "17.00"
        print("MARKETPLACE SELLER FILTER SUMMARY PASS")

        buyer_summary = await skill_marketplace_reporting_service.marketplace_financial_summary(
            db,
            platform_admin_tenant_id=vendor.id,
            seller_tenant_id=seller_b.id,
        )
        assert buyer_summary["verified_settlement_count"] == 0
        assert buyer_summary["verified_paid_purchase_count"] == 0
        print("MARKETPLACE TENANT FILTER ISOLATION PASS")

        await db.rollback()

    async with AsyncSessionLocal() as db:
        tenants = list(
            (
                await db.execute(
                    select(Tenant).where(
                        Tenant.slug.in_(
                            [vendor_slug, seller_a_slug, seller_b_slug, buyer_slug]
                        )
                    )
                )
            ).scalars().all()
        )
        for tenant in tenants:
            if tenant.status != edition_lifecycle_service.STATUS_DEPROVISIONED:
                await edition_lifecycle_service.transition_tenant_status(
                    db,
                    tenant=tenant,
                    target_status=edition_lifecycle_service.STATUS_DEPROVISIONED,
                    actor_id=None,
                    audit_tenant_id=tenant.id,
                    audit_metadata={"certification_fixture": True, "cleanup_mode": "deprovision"},
                )
        await db.commit()
        print("MARKETPLACE REPORTING FIXTURE CLEANUP PASS")


if __name__ == "__main__":
    asyncio.run(verify())
