"""Platform-admin marketplace payout proposals with execution explicitly disabled."""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.skill_marketplace_payout_destination import (
    SkillMarketplacePayoutDestination,
    SkillMarketplacePayoutDestinationStatus,
)
from app.models.skill_marketplace_payout_proposal import (
    SkillMarketplacePayoutExecutionStatus,
    SkillMarketplacePayoutProposal,
    SkillMarketplacePayoutProposalStatus,
)
from app.models.skill_marketplace_settlement import (
    SkillMarketplacePayoutStatus,
    SkillMarketplaceSettlementStatus,
    SkillMarketplaceSettlement,
)
from app.models.tenant import Tenant
from app.models.user import User
from app.services import audit_service


async def create_payout_proposal(
    db: AsyncSession,
    *,
    settlement_id: uuid.UUID,
    platform_admin_tenant_id: uuid.UUID,
    created_by_user_id: uuid.UUID,
) -> SkillMarketplacePayoutProposal:
    """Create or replay a seller payout proposal; never execute a payout."""
    admin_tenant = (
        await db.execute(
            select(Tenant).where(
                Tenant.id == platform_admin_tenant_id,
                Tenant.tenant_kind == "vendor",
                Tenant.status == "active",
            )
        )
    ).scalar_one_or_none()
    if admin_tenant is None:
        raise ValidationAppError("payout proposal requires an active vendor platform-admin tenant")

    admin_user = (
        await db.execute(
            select(User).where(
                User.id == created_by_user_id,
                User.tenant_id == platform_admin_tenant_id,
                User.is_active.is_(True),
                User.is_platform_admin.is_(True),
            )
        )
    ).scalar_one_or_none()
    if admin_user is None:
        raise ValidationAppError("payout proposal requires an active platform administrator")

    settlement = (
        await db.execute(
            select(SkillMarketplaceSettlement)
            .where(
                SkillMarketplaceSettlement.id == settlement_id,
                SkillMarketplaceSettlement.status == SkillMarketplaceSettlementStatus.RECORDED,
                SkillMarketplaceSettlement.payout_status == SkillMarketplacePayoutStatus.NOT_EXECUTED,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if settlement is None:
        raise NotFoundError("recorded marketplace settlement ready for payout proposal was not found")

    existing = (
        await db.execute(
            select(SkillMarketplacePayoutProposal)
            .where(SkillMarketplacePayoutProposal.settlement_id == settlement_id)
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.status == SkillMarketplacePayoutProposalStatus.CANCELLED:
            raise ConflictError("a cancelled payout proposal cannot be recreated for the same settlement")
        return existing

    if settlement.seller_net_amount <= 0:
        raise ValidationAppError("marketplace settlement seller net must be positive before payout proposal")

    destination = (
        await db.execute(
            select(SkillMarketplacePayoutDestination)
            .where(
                SkillMarketplacePayoutDestination.seller_tenant_id == settlement.seller_tenant_id,
                SkillMarketplacePayoutDestination.status == SkillMarketplacePayoutDestinationStatus.ACTIVE,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if destination is None:
        raise ValidationAppError(
            "seller payout destination must be actively bound before payout proposal"
        )

    if destination.seller_tenant_id != settlement.seller_tenant_id:
        raise ValidationAppError("payout destination seller tenant does not match settlement seller tenant")

    proposal = SkillMarketplacePayoutProposal(
        settlement_id=settlement.id,
        seller_tenant_id=settlement.seller_tenant_id,
        platform_admin_tenant_id=platform_admin_tenant_id,
        created_by_user_id=created_by_user_id,
        destination_id=destination.id,
        destination_provider=destination.provider,
        destination_ref=destination.destination_ref,
        amount=Decimal(str(settlement.seller_net_amount)),
        currency=settlement.currency,
        provider="none",
        status=SkillMarketplacePayoutProposalStatus.PROPOSED,
        execution_status=SkillMarketplacePayoutExecutionStatus.NOT_EXECUTED,
        metadata_={
            "seller_payout": "not_executed",
            "provider_execution": "not_configured",
            "tax_treatment": "not_calculated",
            "destination": "bound_snapshot",
            "execution_authority_changed": False,
        },
    )
    db.add(proposal)
    await db.flush()

    await audit_service.record(
        db,
        tenant_id=platform_admin_tenant_id,
        actor_id=created_by_user_id,
        action="skill_marketplace_payout.proposed",
        resource_type="skill_marketplace_payout_proposal",
        resource_id=str(proposal.id),
        metadata={
            "settlement_id": str(settlement.id),
            "seller_tenant_id": str(settlement.seller_tenant_id),
            "destination_id": str(destination.id),
            "destination_provider": destination.provider,
            "destination_bound": True,
            "amount": str(proposal.amount),
            "currency": proposal.currency,
            "provider": "none",
            "seller_payout": "not_executed",
            "tax_treatment": "not_calculated",
            "execution_authority_changed": False,
        },
    )
    await db.flush()
    return proposal


async def list_payout_proposals(
    db: AsyncSession,
    *,
    platform_admin_tenant_id: uuid.UUID,
    status: SkillMarketplacePayoutProposalStatus | None = None,
) -> list[SkillMarketplacePayoutProposal]:
    stmt = select(SkillMarketplacePayoutProposal).where(
        SkillMarketplacePayoutProposal.platform_admin_tenant_id == platform_admin_tenant_id
    )
    if status is not None:
        stmt = stmt.where(SkillMarketplacePayoutProposal.status == status)
    stmt = stmt.order_by(SkillMarketplacePayoutProposal.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())
