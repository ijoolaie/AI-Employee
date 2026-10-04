"""Real PostgreSQL verification of governed marketplace seller payout execution."""
from __future__ import annotations

import asyncio
import os
import time
import uuid
from decimal import Decimal

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.exceptions import ConflictError, ValidationAppError
from app.models.audit_log import AuditLog
from app.models.business_deal import BusinessDeal
from app.models.product import Product
from app.models.skill_marketplace_payout_proposal import (
    SkillMarketplacePayoutExecutionStatus,
    SkillMarketplacePayoutProposalStatus,
)
from app.models.skill_marketplace_purchase import (
    SkillMarketplacePurchase,
    SkillMarketplacePurchaseStatus,
)
from app.models.skill_marketplace_publication import SkillMarketplacePublication
from app.models.skill_marketplace_settlement import (
    SkillMarketplacePayoutStatus,
    SkillMarketplaceSettlement,
    SkillMarketplaceSettlementStatus,
)
from app.models.skill_package import SkillPackage, SkillPackageStatus
from app.models.tenant import Tenant
from app.models.user import User
from app.models.employee import Employee
from app.models.workforce_revenue_event import WorkforceRevenueEvent
from app.services import audit_service, edition_lifecycle_service, skill_marketplace_payout_service
from app.services import skill_marketplace_payout_provider


async def verify() -> None:
    suffix = str(time.time_ns())[-10:]
    slugs = [
        f"w16-payout-seller-{suffix}",
        f"w16-payout-buyer-{suffix}",
        f"w16-payout-platform-{suffix}",
    ]

    async with AsyncSessionLocal() as db:
        seller = Tenant(
            name="W16 Payout Seller",
            slug=slugs[0],
            tenant_kind="customer",
            status="active",
            settings={"marketplace_payout_destination": f"contract://seller/{suffix}"},
        )
        buyer = Tenant(
            name="W16 Payout Buyer",
            slug=slugs[1],
            tenant_kind="customer",
            status="active",
            settings={},
        )
        platform = Tenant(
            name="W16 Payout Platform",
            slug=slugs[2],
            tenant_kind="vendor",
            status="active",
            settings={},
        )
        db.add_all([seller, buyer, platform])
        await db.flush()

        proposer = User(
            tenant_id=platform.id,
            email=f"w16-payout-proposer-{suffix}@example.invalid",
            password_hash="fixture",
            full_name="W16 Payout Proposer",
            is_active=True,
            is_platform_admin=True,
        )
        approver = User(
            tenant_id=platform.id,
            email=f"w16-payout-approver-{suffix}@example.invalid",
            password_hash="fixture",
            full_name="W16 Payout Approver",
            is_active=True,
            is_platform_admin=True,
        )
        executor = User(
            tenant_id=platform.id,
            email=f"w16-payout-executor-{suffix}@example.invalid",
            password_hash="fixture",
            full_name="W16 Payout Executor",
            is_active=True,
            is_platform_admin=True,
        )
        db.add_all([proposer, approver, executor])
        await db.flush()

        buyer_employee = Employee(
            tenant_id=buyer.id,
            slug=f"w16-payout-buyer-employee-{suffix}",
            name="Buyer Employee",
            kind="custom",
            is_active=True,
        )
        db.add(buyer_employee)
        await db.flush()

        product = Product(
            tenant_id=seller.id,
            sku=f"W16-PAYOUT-{suffix}",
            name="Payout Skill Product",
            description="Payout execution fixture",
            category="employee_skill",
            price=Decimal("100.00"),
            currency="EUR",
            inventory=10,
            attributes={},
            is_active=True,
        )
        db.add(product)
        await db.flush()

        package = SkillPackage(
            tenant_id=seller.id,
            product_id=product.id,
            slug=f"w16-payout-skill-{suffix}",
            name="Payout Skill",
            version=1,
            status=SkillPackageStatus.PUBLISHED,
            manifest={},
            compatibility={},
            presentation_metadata={},
        )
        db.add(package)
        await db.flush()

        publication = SkillMarketplacePublication(
            owner_tenant_id=seller.id,
            skill_package_id=package.id,
            visibility="public",
            title="Payout Skill",
            summary="Fixture",
        )
        db.add(publication)
        await db.flush()

        deal = BusinessDeal(
            tenant_id=buyer.id,
            title="Marketplace payout fixture deal",
            customer_name="W16 Buyer",
            customer_email="buyer@example.invalid",
            stage="won",
            amount=Decimal("100.00"),
            currency="EUR",
            probability=100,
            metadata_={},
        )
        db.add(deal)
        await db.flush()

        purchase = SkillMarketplacePurchase(
            buyer_tenant_id=buyer.id,
            seller_tenant_id=seller.id,
            publication_id=publication.id,
            employee_id=buyer_employee.id,
            skill_package_id=package.id,
            product_id=product.id,
            business_deal_id=deal.id,
            idempotency_key=f"w16-payout-purchase-{suffix}",
            provider="contract-test",
            provider_event_id=f"purchase-event-{suffix}",
            status=SkillMarketplacePurchaseStatus.PAID,
            amount=Decimal("100.00"),
            currency="EUR",
            metadata_={},
        )
        db.add(purchase)
        await db.flush()

        revenue = WorkforceRevenueEvent(
            tenant_id=buyer.id,
            deal_id=deal.id,
            provider="contract-test",
            provider_event_id=f"revenue-event-{suffix}",
            amount=Decimal("100.00"),
            currency="EUR",
            verified_at=deal.created_at or __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            source="w16-marketplace-payout-e2e",
            metadata_={"seller_tenant_id": str(seller.id)},
        )
        db.add(revenue)
        await db.flush()

        settlement = SkillMarketplaceSettlement(
            purchase_id=purchase.id,
            revenue_event_id=revenue.id,
            buyer_tenant_id=buyer.id,
            seller_tenant_id=seller.id,
            provider="contract-test",
            provider_event_id=f"settlement-event-{suffix}",
            gross_amount=Decimal("100.00"),
            platform_fee_bps=1000,
            platform_fee_amount=Decimal("10.00"),
            seller_net_amount=Decimal("90.00"),
            currency="EUR",
            status=SkillMarketplaceSettlementStatus.RECORDED,
            payout_status=SkillMarketplacePayoutStatus.NOT_EXECUTED,
            metadata_={"tax_treatment": "not_calculated"},
            verified_at=revenue.verified_at,
        )
        db.add(settlement)
        await db.commit()

        settings = __import__("app.core.config", fromlist=["get_settings"]).get_settings()
        settings.skill_marketplace_payout_provider_name = os.environ.get(
            "SKILL_MARKETPLACE_PAYOUT_PROVIDER_NAME", "none"
        )

        # Verify the default remains fail-closed before enabling the deterministic
        # CI contract provider for the positive execution path.
        settings.skill_marketplace_payout_provider_name = "none"
        proposal = await skill_marketplace_payout_service.create_payout_proposal(
            db,
            settlement_id=settlement.id,
            platform_admin_tenant_id=platform.id,
            created_by_user_id=proposer.id,
        )
        await db.commit()
        assert proposal.status == SkillMarketplacePayoutProposalStatus.PROPOSED
        assert proposal.execution_status == SkillMarketplacePayoutExecutionStatus.NOT_EXECUTED

        try:
            await skill_marketplace_payout_service.execute_payout_proposal(
                db,
                proposal_id=proposal.id,
                platform_admin_tenant_id=platform.id,
                executed_by_user_id=executor.id,
            )
        except (ValidationAppError, ConflictError) as exc:
            assert "provider" in str(exc).lower() or "configured" in str(exc).lower()
            print("PAYOUT DEFAULT PROVIDER FAIL-CLOSED PASS")
        else:
            raise AssertionError("unconfigured payout provider unexpectedly executed")

        settings.skill_marketplace_payout_provider_name = "contract-test"

        try:
            await skill_marketplace_payout_service.approve_payout_proposal(
                db,
                proposal_id=proposal.id,
                platform_admin_tenant_id=platform.id,
                decided_by_user_id=proposer.id,
                decision="approve",
            )
        except ConflictError as exc:
            assert "creator cannot approve" in str(exc)
            print("PAYOUT SEPARATION OF DUTIES CREATOR REJECT PASS")
        else:
            raise AssertionError("proposal creator was allowed to approve")

        approval = await skill_marketplace_payout_service.approve_payout_proposal(
            db,
            proposal_id=proposal.id,
            platform_admin_tenant_id=platform.id,
            decided_by_user_id=approver.id,
            decision="approve",
            reason="fixture approval",
        )
        await db.commit()
        assert approval.status.value == "approved"
        print("PAYOUT HUMAN APPROVAL PASS")

        try:
            await skill_marketplace_payout_service.execute_payout_proposal(
                db,
                proposal_id=proposal.id,
                platform_admin_tenant_id=platform.id,
                executed_by_user_id=approver.id,
            )
        except ConflictError as exc:
            assert "approver cannot be the same" in str(exc)
            print("PAYOUT SEPARATION OF DUTIES EXECUTOR REJECT PASS")
        else:
            raise AssertionError("approver was allowed to execute the same payout")

        executed = await skill_marketplace_payout_service.execute_payout_proposal(
            db,
            proposal_id=proposal.id,
            platform_admin_tenant_id=platform.id,
            executed_by_user_id=executor.id,
        )
        await db.commit()
        assert executed.execution_status == SkillMarketplacePayoutExecutionStatus.EXECUTED
        assert executed.provider == "contract-test"
        assert executed.provider_payout_id == f"contract-payout-{proposal.id}"
        assert executed.executed_at is not None
        assert settlement.payout_status == SkillMarketplacePayoutStatus.EXECUTED
        print("PAYOUT CONTRACT PROVIDER EXECUTION PASS")
        print("PAYOUT SETTLEMENT STATE PROPAGATION PASS")

        replay = await skill_marketplace_payout_service.execute_payout_proposal(
            db,
            proposal_id=proposal.id,
            platform_admin_tenant_id=platform.id,
            executed_by_user_id=executor.id,
        )
        assert replay.id == executed.id
        assert replay.provider_payout_id == executed.provider_payout_id
        assert replay.execution_status == SkillMarketplacePayoutExecutionStatus.EXECUTED
        print("PAYOUT EXECUTION IDEMPOTENCY PASS")

        logs = list(
            (
                await db.execute(
                    select(AuditLog).where(
                        AuditLog.tenant_id == platform.id,
                        AuditLog.resource_id == str(proposal.id),
                    )
                )
            ).scalars().all()
        )
        actions = {item.action for item in logs}
        assert "skill_marketplace_payout.proposed" in actions
        assert "skill_marketplace_payout.approval_decided" in actions
        assert "skill_marketplace_payout.executed" in actions
        execution_log = [item for item in logs if item.action == "skill_marketplace_payout.executed"][-1]
        assert (execution_log.metadata_ or {}).get("execution_authority_changed") is False
        print("PAYOUT AUDIT PROVENANCE PASS")

        # Cross-tenant platform admin rejection.
        outsider = Tenant(
            name="W16 Payout Outsider",
            slug=f"w16-payout-outsider-{suffix}",
            tenant_kind="vendor",
            status="active",
            settings={},
        )
        db.add(outsider)
        await db.flush()
        outsider_user = User(
            tenant_id=outsider.id,
            email=f"w16-payout-outsider-{suffix}@example.invalid",
            password_hash="fixture",
            full_name="W16 Payout Outsider",
            is_active=True,
            is_platform_admin=True,
        )
        db.add(outsider_user)
        await db.flush()
        try:
            await skill_marketplace_payout_service.execute_payout_proposal(
                db,
                proposal_id=proposal.id,
                platform_admin_tenant_id=outsider.id,
                executed_by_user_id=outsider_user.id,
            )
        except (ValidationAppError, NotFoundError, ConflictError) as exc:
            assert "payout" in str(exc).lower() or "tenant" in str(exc).lower()
            print("PAYOUT CROSS-TENANT ADMIN REJECT PASS")
        else:
            raise AssertionError("cross-tenant platform admin executed payout")

        await db.rollback()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant).where(Tenant.slug.in_(slugs)))
        tenants = list(result.scalars().all())
        for tenant in tenants:
            await edition_lifecycle_service.transition_tenant_status(
                db,
                tenant=tenant,
                target_status=edition_lifecycle_service.STATUS_DEPROVISIONED,
                actor_id=None,
                audit_tenant_id=tenant.id,
                audit_metadata={"certification_fixture": True, "cleanup_mode": "deprovision"},
            )
        await db.commit()

    print("W16 MARKETPLACE PAYOUT EXECUTION REAL-STACK PASS")


if __name__ == "__main__":
    asyncio.run(verify())
