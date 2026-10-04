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
from app.models.employee import Employee, EmployeeVersion
from app.models.run import Run
from app.models.skill_marketplace_purchase import SkillMarketplacePurchase, SkillMarketplacePurchaseStatus
from app.models.skill_package import EmployeeSkillInstallation, EmployeeSkillInstallationStatus, SkillPackage, SkillPackageStatus
from app.models.skill_purchase_entitlement import SkillPurchaseEntitlement, SkillPurchaseEntitlementStatus
from app.models.tenant import Tenant
from app.models.workforce_revenue_event import WorkforceRevenueEvent
from app.models.user import User
from app.models.skill_marketplace_payout_proposal import SkillMarketplacePayoutExecutionStatus, SkillMarketplacePayoutProposalStatus
from app.models.skill_marketplace_settlement import SkillMarketplacePayoutStatus, SkillMarketplaceSettlement, SkillMarketplaceSettlementStatus
from app.services import edition_lifecycle_service, skill_marketplace_service, stripe_service
from app.services.skill_marketplace_publication_service import SkillMarketplacePublicationService
from app.services.skill_marketplace_purchase_service import create_checkout
from app.services.skill_marketplace_payout_destination import bind_payout_destination, revoke_payout_destination
from app.services import approval_service
from app.services.skill_marketplace_payout_service import (
    create_payout_proposal,
    execute_payout_proposal,
    list_payout_proposals,
)


async def verify() -> None:
    suffix = str(time.time_ns())[-12:]
    vendor_slug = f"w16-marketplace-vendor-{suffix}"
    seller_slug = f"w16-marketplace-seller-{suffix}"
    buyer_slug = f"w16-marketplace-buyer-{suffix}"
    settings = get_settings()
    settings.sales_payment_provider_name = "contract-test"
    settings.skill_marketplace_settlement_enabled = True
    settings.skill_marketplace_platform_fee_bps = 1500

    async with AsyncSessionLocal() as db:
        vendor = Tenant(name="W16 Marketplace Vendor", slug=vendor_slug, tenant_kind="vendor")
        seller = Tenant(name="W16 Marketplace Seller", slug=seller_slug)
        buyer = Tenant(name="W16 Marketplace Buyer", slug=buyer_slug)
        db.add_all([vendor, seller, buyer])
        await db.flush()
        seller_actor = User(
            tenant_id=seller.id,
            email=f"w16-marketplace-seller-{suffix}@example.test",
            password_hash="certification-fixture",
            full_name="W16 Marketplace Seller Actor",
            is_active=True,
            is_platform_admin=False,
        )
        db.add(seller_actor)
        await db.flush()
        platform_admin = User(
            tenant_id=vendor.id,
            email=f"w16-marketplace-admin-{suffix}@example.test",
            password_hash="certification-fixture",
            full_name="W16 Marketplace Platform Admin",
            is_active=True,
            is_platform_admin=True,
        )
        approval_decider = User(
            tenant_id=vendor.id,
            email=f"w16-marketplace-approval-{suffix}@example.test",
            password_hash="certification-fixture",
            full_name="W16 Marketplace Approval Decider",
            is_active=True,
            is_platform_admin=True,
        )
        db.add_all([platform_admin, approval_decider])
        await db.flush()

        governance_employee = Employee(
            tenant_id=vendor.id,
            slug=f"w16-marketplace-payout-governance-{suffix}",
            name="Marketplace Payout Governance Employee",
            kind="custom",
            is_active=True,
        )
        db.add(governance_employee)
        await db.flush()
        governance_version = EmployeeVersion(
            employee_id=governance_employee.id,
            version_number=1,
            is_current=True,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            prompt_template="W16 payout governance fixture",
            allowed_tools=["marketplace_execute_payout"],
            rules={},
        )
        db.add(governance_version)
        await db.flush()
        governance_run = Run(
            tenant_id=vendor.id,
            employee_id=governance_employee.id,
            employee_version_id=governance_version.id,
            created_by=platform_admin.id,
            status="pending",
            input_data={},
            request_id=f"w16-payout-run-{suffix}",
        )
        db.add(governance_run)
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

        destination = await bind_payout_destination(
            db,
            seller_tenant_id=seller.id,
            provider="contract-test",
            destination_ref=f"seller-destination-{suffix}-v1",
            actor_user_id=seller_actor.id,
        )
        assert destination.seller_tenant_id == seller.id
        assert destination.provider == "contract-test"
        print("MARKETPLACE SELLER PAYOUT DESTINATION BINDING PASS")

        proposal = await create_payout_proposal(
            db,
            settlement_id=settlement.id,
            platform_admin_tenant_id=vendor.id,
            created_by_user_id=platform_admin.id,
        )
        assert proposal.status == SkillMarketplacePayoutProposalStatus.PROPOSED
        assert proposal.execution_status == SkillMarketplacePayoutExecutionStatus.NOT_EXECUTED
        assert proposal.seller_tenant_id == seller.id
        assert proposal.platform_admin_tenant_id == vendor.id
        assert proposal.amount == settlement.seller_net_amount
        assert proposal.currency == settlement.currency
        assert proposal.provider == "none"
        assert proposal.destination_id == destination.id
        assert proposal.destination_provider == "contract-test"
        assert proposal.destination_ref == f"seller-destination-{suffix}-v1"
        assert proposal.metadata_["destination"] == "bound_snapshot"
        assert proposal.metadata_["seller_payout"] == "not_executed"
        print("MARKETPLACE SELLER PAYOUT PROPOSAL CREATION PASS")
        await revoke_payout_destination(
            db,
            seller_tenant_id=seller.id,
            actor_user_id=seller_actor.id,
        )
        replacement = await bind_payout_destination(
            db,
            seller_tenant_id=seller.id,
            provider="contract-test",
            destination_ref=f"seller-destination-{suffix}-v2",
            actor_user_id=seller_actor.id,
        )
        assert replacement.id != destination.id
        await db.refresh(proposal)
        assert proposal.destination_id == destination.id
        assert proposal.destination_ref == f"seller-destination-{suffix}-v1"
        assert proposal.destination_ref != replacement.destination_ref
        print("MARKETPLACE PAYOUT PROPOSAL DESTINATION IMMUTABLE SNAPSHOT PASS")


        settings.marketplace_payout_provider_name = "contract-test"
        approval = await approval_service.create_request(
            db,
            run=governance_run,
            tool_name="marketplace_execute_payout",
            tool_call_id=f"w16-marketplace-payout-{suffix}",
            arguments={"proposal_id": str(proposal.id)},
            continuation_messages=[],
            tenant_id=vendor.id,
            requested_by=platform_admin.id,
        )
        assert approval.status == "pending"
        decided = await approval_service.decide(
            db,
            approval_id=approval.id,
            tenant_id=vendor.id,
            decided_by=approval_decider.id,
            decision="approve",
            reason="W16 deterministic payout execution certification fixture",
        )
        assert decided.status == "approved"

        executed = await execute_payout_proposal(
            db,
            proposal_id=proposal.id,
            platform_admin_tenant_id=vendor.id,
            actor_user_id=approval_decider.id,
            approval_granted=True,
            approval_request_id=approval.id,
        )
        assert executed.execution_status == SkillMarketplacePayoutExecutionStatus.ACCEPTED
        assert executed.provider == "contract-test"
        assert executed.executed is False
        assert executed.external_execution is False
        assert executed.provider_payout_id == f"contract-payout-{executed.idempotency_key}"
        assert executed.provider_event_id == f"contract-payout-event-{executed.idempotency_key}"
        assert executed.metadata_["approval_required"] is True
        assert executed.metadata_["approval_granted"] is True
        assert executed.metadata_["destination"] == "bound_snapshot"
        print("MARKETPLACE PAYOUT EXPLICIT APPROVAL PASS")
        print("MARKETPLACE PAYOUT GOVERNED CONTRACT-TEST EXECUTION PASS")
        print("MARKETPLACE PAYOUT EXTERNAL EXECUTION FALSE PASS")

        replay_proposal = await create_payout_proposal(
            db,
            settlement_id=settlement.id,
            platform_admin_tenant_id=vendor.id,
            created_by_user_id=platform_admin.id,
        )
        assert replay_proposal.id == proposal.id
        proposals = await list_payout_proposals(
            db,
            platform_admin_tenant_id=vendor.id,
            status=SkillMarketplacePayoutProposalStatus.PROPOSED,
        )
        assert len(proposals) == 1
        print("MARKETPLACE SELLER PAYOUT PROPOSAL IDEMPOTENCY PASS")

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
        settlement_count = (
            await db.execute(
                select(func.count()).select_from(SkillMarketplaceSettlement).where(
                    SkillMarketplaceSettlement.purchase_id == purchase.id
                )
            )
        ).scalar_one()
        revenue_count = (
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
                    select(Tenant).where(Tenant.slug.in_([vendor_slug, seller_slug, buyer_slug]))
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
