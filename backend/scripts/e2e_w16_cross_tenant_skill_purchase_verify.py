"""Real-stack cross-tenant Skill Marketplace purchase and settlement verification."""
from __future__ import annotations

import asyncio
import time
import uuid

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import ConflictError, NotFoundError
from app.models.business_order import BusinessOrder
from app.models.employee import Employee
from app.models.skill_marketplace_purchase import SkillMarketplacePurchase, SkillMarketplacePurchaseStatus
from app.models.skill_package import EmployeeSkillInstallation, EmployeeSkillInstallationStatus, SkillPackage, SkillPackageStatus
from app.models.skill_purchase_entitlement import SkillPurchaseEntitlement, SkillPurchaseEntitlementStatus
from app.models.tenant import Tenant
from app.models.workforce_revenue_event import WorkforceRevenueEvent
from app.models.skill_marketplace_settlement import SkillMarketplacePayoutStatus, SkillMarketplaceSettlement, SkillMarketplaceSettlementStatus
from app.services import edition_lifecycle_service, skill_marketplace_service, stripe_service
from app.services.skill_marketplace_publication_service import SkillMarketplacePublicationService
from app.services.skill_marketplace_purchase_service import create_checkout


async def verify() -> None:
    suffix = str(time.time_ns())[-12:]
    seller_slug = f"w16-marketplace-seller-{suffix}"
    buyer_slug = f"w16-marketplace-buyer-{suffix}"
    settings = get_settings()
    settings.sales_payment_provider_name = "contract-test"
    settings.skill_marketplace_settlement_enabled = True
    settings.skill_marketplace_platform_fee_bps = 1500

    async with AsyncSessionLocal() as db:
        seller = Tenant(name="W16 Marketplace Seller", slug=seller_slug)
        buyer = Tenant(name="W16 Marketplace Buyer", slug=buyer_slug)
        db.add_all([seller, buyer])
        await db.flush()

        employee = Employee(
            tenant_id=buyer.id,
            slug=f"w16-marketplace-buyer-employee-{suffix}",
            name="Marketplace Buyer Employee",
            kind="custom",
            is_active=True,
        )
        db.add(employee)
        await db.flush()

        product = __import__("app.models.product", fromlist=["Product"]).Product(
            tenant_id=seller.id,
            sku=f"w16-marketplace-skill-{suffix}",
            name="Marketplace Sales Skill",
            description="Cross-tenant marketplace skill fixture",
            category="employee_skill",
            price=10,
            currency="EUR",
            inventory=10,
            attributes={
                "skill_package_slug": f"marketplace-skill-{suffix}",
                "skill_package_version": 1,
            },
            is_active=True,
        )
        db.add(product)
        await db.flush()

        package = await skill_marketplace_service.create_package(
            db,
            tenant_id=seller.id,
            slug=product.attributes["skill_package_slug"],
            name="Marketplace Sales Skill",
            version=1,
            product_id=product.id,
            manifest={"contract_version": "w16-marketplace-v1"},
        )
        await skill_marketplace_service.publish_package(
            db,
            tenant_id=seller.id,
            package_id=package.id,
            actor_id=None,
        )
        publication = await SkillMarketplacePublicationService.publish(
            db,
            owner_tenant_id=seller.id,
            skill_package_id=package.id,
            actor_id=None,
            visibility="public",
            title="Marketplace Sales Skill",
            summary="Public purchase fixture",
        )
        await db.commit()

        purchase, deal, result, replay = await create_checkout(
            db,
            buyer_tenant_id=buyer.id,
            employee_id=employee.id,
            publication_id=publication.id,
            actor_id=None,
            customer_email="buyer@example.test",
            idempotency_key=f"w16-marketplace-{suffix}",
        )
        assert replay is False
        assert purchase.buyer_tenant_id == buyer.id
        assert purchase.seller_tenant_id == seller.id
        assert purchase.status == SkillMarketplacePurchaseStatus.PENDING
        assert deal.tenant_id == buyer.id
        assert (deal.metadata_ or {})["skill_marketplace_purchase"]["purchase_id"] == str(purchase.id)
        assert result is not None
        assert result.provider == "contract-test"
        print("CROSS-TENANT MARKETPLACE CHECKOUT PREPARED PASS")

        replay_purchase, replay_deal, replay_result, replay_flag = await create_checkout(
            db,
            buyer_tenant_id=buyer.id,
            employee_id=employee.id,
            publication_id=publication.id,
            actor_id=None,
            customer_email="buyer@example.test",
            idempotency_key=f"w16-marketplace-{suffix}",
        )
        assert replay_flag is True
        assert replay_purchase.id == purchase.id
        assert replay_deal.id == deal.id
        assert replay_result is not None
        print("CROSS-TENANT MARKETPLACE CHECKOUT IDEMPOTENCY PASS")

        payment_event_id = f"evt_w16_marketplace_{suffix}"
        _, order_id = await stripe_service.apply_verified_sales_payment(
            db,
            provider="stripe",
            provider_event_id=payment_event_id,
            data={
                "id": payment_event_id,
                "amount_received": 1000,
                "currency": "eur",
                "metadata": {
                    "tenant_id": str(buyer.id),
                    "sales_deal_id": str(deal.id),
                },
            },
        )
        assert order_id is not None

        purchase = await db.get(SkillMarketplacePurchase, purchase.id)
        assert purchase is not None
        assert purchase.status == SkillMarketplacePurchaseStatus.PAID
        installation = (
            await db.execute(
                select(EmployeeSkillInstallation).where(
                    EmployeeSkillInstallation.tenant_id == buyer.id,
                    EmployeeSkillInstallation.employee_id == employee.id,
                    EmployeeSkillInstallation.skill_package_id == package.id,
                    EmployeeSkillInstallation.status == EmployeeSkillInstallationStatus.ACTIVE,
                )
            )
        ).scalar_one()
        assert installation.source_owner_tenant_id == seller.id

        entitlement = (
            await db.execute(
                select(SkillPurchaseEntitlement).where(
                    SkillPurchaseEntitlement.tenant_id == buyer.id,
                    SkillPurchaseEntitlement.employee_id == employee.id,
                    SkillPurchaseEntitlement.skill_package_id == package.id,
                    SkillPurchaseEntitlement.status == SkillPurchaseEntitlementStatus.ACTIVE,
                )
            )
        ).scalar_one()
        assert entitlement.source_owner_tenant_id == seller.id
        assert entitlement.source_publication_id == publication.id

        revenue = (
            await db.execute(
                select(WorkforceRevenueEvent).where(
                    WorkforceRevenueEvent.provider == "stripe",
                    WorkforceRevenueEvent.provider_event_id == payment_event_id,
                )
            )
        ).scalar_one()
        assert (revenue.metadata_ or {})["skill_marketplace_purchase_id"] == str(purchase.id)
        assert (revenue.metadata_ or {})["skill_marketplace_seller_tenant_id"] == str(seller.id)
        assert (revenue.metadata_ or {})["source"] == "skill_marketplace"
        print("CROSS-TENANT MARKETPLACE PAYMENT + ENTITLEMENT + INSTALLATION PASS")
        print("CROSS-TENANT MARKETPLACE REVENUE EVENT CORRELATION PASS")

        settlement = (
            await db.execute(
                select(SkillMarketplaceSettlement).where(
                    SkillMarketplaceSettlement.purchase_id == purchase.id,
                )
            )
        ).scalar_one()
        assert settlement.status == SkillMarketplaceSettlementStatus.RECORDED
        assert settlement.payout_status == SkillMarketplacePayoutStatus.NOT_EXECUTED
        assert settlement.buyer_tenant_id == buyer.id
        assert settlement.seller_tenant_id == seller.id
        assert settlement.provider == "stripe"
        assert settlement.provider_event_id == payment_event_id
        assert settlement.gross_amount == purchase.amount
        assert settlement.platform_fee_bps == 1500
        assert settlement.platform_fee_amount == purchase.amount * 15 / 100
        assert settlement.seller_net_amount == purchase.amount - settlement.platform_fee_amount
        assert settlement.metadata_["seller_payout"] == "not_executed"
        assert settlement.metadata_["tax_treatment"] == "not_calculated"
        print("CROSS-TENANT MARKETPLACE SETTLEMENT SPLIT PASS")

        duplicate_tenant, duplicate_order = await stripe_service.apply_verified_sales_payment(
            db,
            provider="stripe",
            provider_event_id=payment_event_id,
            data={
                "id": payment_event_id,
                "amount_received": 1000,
                "currency": "eur",
                "metadata": {
                    "tenant_id": str(buyer.id),
                    "sales_deal_id": str(deal.id),
                },
            },
        )
        assert duplicate_tenant == buyer.id
        assert duplicate_order == order_id

        purchase_count = (
            await db.execute(
                select(func.count()).select_from(SkillMarketplacePurchase).where(
                    SkillMarketplacePurchase.id == purchase.id
                )
            )
        ).scalar_one()
        entitlement_count = (
            await db.execute(
                select(func.count()).select_from(SkillPurchaseEntitlement).where(
                    SkillPurchaseEntitlement.tenant_id == buyer.id,
                    SkillPurchaseEntitlement.employee_id == employee.id,
                    SkillPurchaseEntitlement.skill_package_id == package.id,
                )
            )
        ).scalar_one()
        install_count = (
            await db.execute(
                select(func.count()).select_from(EmployeeSkillInstallation).where(
                    EmployeeSkillInstallation.tenant_id == buyer.id,
                    EmployeeSkillInstallation.employee_id == employee.id,
                    EmployeeSkillInstallation.skill_package_id == package.id,
                )
            )
        ).scalar_one()
        settlement_count = (            await db.execute(                select(func.count()).select_from(SkillMarketplaceSettlement).where(                    SkillMarketplaceSettlement.purchase_id == purchase.id                )            )        ).scalar_one()        revenue_count = (
            await db.execute(
                select(func.count()).select_from(WorkforceRevenueEvent).where(
                    WorkforceRevenueEvent.provider == "stripe",
                    WorkforceRevenueEvent.provider_event_id == payment_event_id,
                )
            )
        ).scalar_one()
        assert purchase_count == 1
        assert entitlement_count == 1
        assert install_count == 1
        assert revenue_count == 1
        assert settlement_count == 1
        print("CROSS-TENANT MARKETPLACE PAYMENT REPLAY IDEMPOTENCY PASS")

        try:
            await skill_marketplace_service.install(
                db,
                tenant_id=buyer.id,
                employee_id=employee.id,
                skill_package_id=package.id,
            )
        except (NotFoundError, ConflictError):
            print("CROSS-TENANT DIRECT INSTALL WITHOUT PUBLICATION REJECT PASS")
        else:
            raise AssertionError("buyer installed seller package without marketplace publication")

        await db.rollback()

    async with AsyncSessionLocal() as db:
        tenants = list(
            (
                await db.execute(
                    select(Tenant).where(Tenant.slug.in_([seller_slug, buyer_slug]))
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
        print("CROSS-TENANT MARKETPLACE FIXTURE CLEANUP PASS")


if __name__ == "__main__":
    asyncio.run(verify())
