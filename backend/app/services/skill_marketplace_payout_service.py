"""Governed platform-admin marketplace seller payout service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.skill_marketplace_payout_approval import (
    SkillMarketplacePayoutApproval,
    SkillMarketplacePayoutApprovalStatus,
)
from app.models.skill_marketplace_payout_proposal import (
    SkillMarketplacePayoutExecutionStatus,
    SkillMarketplacePayoutProposal,
    SkillMarketplacePayoutProposalStatus,
)
from app.models.skill_marketplace_settlement import (
    SkillMarketplacePayoutStatus,
    SkillMarketplaceSettlement,
    SkillMarketplaceSettlementStatus,
)
from app.models.tenant import Tenant
from app.models.user import User
from app.services import audit_service
from app.services.skill_marketplace_payout_provider import (
    MarketplacePayoutProviderError,
    MarketplacePayoutProviderUnknown,
    get_marketplace_payout_provider,
)


async def _assert_platform_admin(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[Tenant, User]:
    tenant = (
        await db.execute(
            select(Tenant).where(
                Tenant.id == tenant_id,
                Tenant.tenant_kind == "vendor",
                Tenant.status == "active",
            )
        )
    ).scalar_one_or_none()
    if tenant is None:
        raise ValidationAppError(
            "marketplace payout requires an active vendor platform-admin tenant"
        )
    user = (
        await db.execute(
            select(User).where(
                User.id == user_id,
                User.tenant_id == tenant_id,
                User.is_active.is_(True),
                User.is_platform_admin.is_(True),
            )
        )
    ).scalar_one_or_none()
    if user is None:
        raise ValidationAppError(
            "marketplace payout requires an active platform administrator"
        )
    return tenant, user


async def create_payout_proposal(
    db: AsyncSession,
    *,
    settlement_id: uuid.UUID,
    platform_admin_tenant_id: uuid.UUID,
    created_by_user_id: uuid.UUID,
) -> SkillMarketplacePayoutProposal:
    await _assert_platform_admin(
        db,
        tenant_id=platform_admin_tenant_id,
        user_id=created_by_user_id,
    )
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
        raise NotFoundError(
            "recorded marketplace settlement ready for payout proposal was not found"
        )

    existing = (
        await db.execute(
            select(SkillMarketplacePayoutProposal).where(
                SkillMarketplacePayoutProposal.settlement_id == settlement_id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.status == SkillMarketplacePayoutProposalStatus.CANCELLED:
            raise ConflictError(
                "a cancelled payout proposal cannot be recreated for the same settlement"
            )
        return existing

    if settlement.seller_net_amount <= 0:
        raise ValidationAppError(
            "marketplace settlement seller net must be positive before payout proposal"
        )

    proposal = SkillMarketplacePayoutProposal(
        settlement_id=settlement.id,
        seller_tenant_id=settlement.seller_tenant_id,
        platform_admin_tenant_id=platform_admin_tenant_id,
        created_by_user_id=created_by_user_id,
        amount=Decimal(str(settlement.seller_net_amount)),
        currency=settlement.currency,
        provider="none",
        status=SkillMarketplacePayoutProposalStatus.PROPOSED,
        execution_status=SkillMarketplacePayoutExecutionStatus.NOT_EXECUTED,
        metadata_={
            "seller_payout": "not_executed",
            "provider_execution": "not_configured",
            "tax_treatment": "not_calculated",
            "destination": "not_configured",
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
            "amount": str(proposal.amount),
            "currency": proposal.currency,
            "provider": "none",
            "seller_payout": "not_executed",
            "tax_treatment": "not_calculated",
            "execution_authority_changed": False,
        },
    )
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


async def approve_payout_proposal(
    db: AsyncSession,
    *,
    proposal_id: uuid.UUID,
    platform_admin_tenant_id: uuid.UUID,
    decided_by_user_id: uuid.UUID,
    decision: str,
    reason: str | None = None,
) -> SkillMarketplacePayoutApproval:
    await _assert_platform_admin(
        db,
        tenant_id=platform_admin_tenant_id,
        user_id=decided_by_user_id,
    )
    decision = str(decision).strip().lower()
    if decision not in {"approve", "reject"}:
        raise ValidationAppError("payout approval decision must be approve or reject")

    proposal = (
        await db.execute(
            select(SkillMarketplacePayoutProposal).where(
                SkillMarketplacePayoutProposal.id == proposal_id,
                SkillMarketplacePayoutProposal.platform_admin_tenant_id == platform_admin_tenant_id,
            ).with_for_update()
        )
    ).scalar_one_or_none()
    if proposal is None:
        raise NotFoundError("marketplace payout proposal not found")
    if proposal.status != SkillMarketplacePayoutProposalStatus.PROPOSED:
        raise ConflictError(
            f"payout proposal is not approvable: {proposal.status.value}"
        )
    if proposal.created_by_user_id == decided_by_user_id:
        raise ConflictError("payout proposal creator cannot approve the same payout")

    existing = (
        await db.execute(
            select(SkillMarketplacePayoutApproval).where(
                SkillMarketplacePayoutApproval.proposal_id == proposal_id
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("payout proposal already has an approval decision")

    approval = SkillMarketplacePayoutApproval(
        proposal_id=proposal_id,
        platform_admin_tenant_id=platform_admin_tenant_id,
        decided_by_user_id=decided_by_user_id,
        status=(
            SkillMarketplacePayoutApprovalStatus.APPROVED
            if decision == "approve"
            else SkillMarketplacePayoutApprovalStatus.REJECTED
        ),
        reason=(reason or "")[:2000] or None,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(approval)
    await db.flush()
    await audit_service.record(
        db,
        tenant_id=platform_admin_tenant_id,
        actor_id=decided_by_user_id,
        action="skill_marketplace_payout.approval_decided",
        resource_type="skill_marketplace_payout_proposal",
        resource_id=str(proposal.id),
        metadata={
            "approval_id": str(approval.id),
            "decision": approval.status.value,
            "seller_tenant_id": str(proposal.seller_tenant_id),
            "amount": str(proposal.amount),
            "currency": proposal.currency,
            "separation_of_duties": True,
        },
    )
    return approval


async def execute_payout_proposal(
    db: AsyncSession,
    *,
    proposal_id: uuid.UUID,
    platform_admin_tenant_id: uuid.UUID,
    executed_by_user_id: uuid.UUID,
) -> SkillMarketplacePayoutProposal:
    await _assert_platform_admin(
        db,
        tenant_id=platform_admin_tenant_id,
        user_id=executed_by_user_id,
    )

    # Lock order is settlement -> proposal everywhere this service mutates
    # payout state. This prevents the create/execute paths from deadlocking.
    proposal_identity = (
        await db.execute(
            select(
                SkillMarketplacePayoutProposal.id,
                SkillMarketplacePayoutProposal.settlement_id,
            ).where(
                SkillMarketplacePayoutProposal.id == proposal_id,
                SkillMarketplacePayoutProposal.platform_admin_tenant_id == platform_admin_tenant_id,
            )
        )
    ).one_or_none()
    if proposal_identity is None:
        raise NotFoundError("marketplace payout proposal not found")

    settlement = (
        await db.execute(
            select(SkillMarketplaceSettlement).where(
                SkillMarketplaceSettlement.id == proposal_identity.settlement_id
            ).with_for_update()
        )
    ).scalar_one_or_none()
    if settlement is None:
        raise NotFoundError("marketplace settlement for payout proposal was not found")

    proposal = (
        await db.execute(
            select(SkillMarketplacePayoutProposal).where(
                SkillMarketplacePayoutProposal.id == proposal_id,
                SkillMarketplacePayoutProposal.platform_admin_tenant_id == platform_admin_tenant_id,
            ).with_for_update()
        )
    ).scalar_one_or_none()
    if proposal is None:
        raise NotFoundError("marketplace payout proposal not found")

    if proposal.execution_status == SkillMarketplacePayoutExecutionStatus.EXECUTED:
        return proposal
    if proposal.execution_status == SkillMarketplacePayoutExecutionStatus.UNKNOWN:
        raise ConflictError(
            "payout provider outcome is unknown; manual reconciliation is required"
        )
    if proposal.status != SkillMarketplacePayoutProposalStatus.PROPOSED:
        raise ConflictError("cancelled payout proposal cannot be executed")
    if settlement.payout_status != SkillMarketplacePayoutStatus.NOT_EXECUTED:
        raise ConflictError(
            "marketplace settlement payout status no longer permits execution"
        )
    if (
        proposal.seller_tenant_id != settlement.seller_tenant_id
        or proposal.amount != settlement.seller_net_amount
        or proposal.currency != settlement.currency
    ):
        raise ConflictError("payout proposal no longer matches its settlement")

    approval = (
        await db.execute(
            select(SkillMarketplacePayoutApproval).where(
                SkillMarketplacePayoutApproval.proposal_id == proposal_id,
                SkillMarketplacePayoutApproval.platform_admin_tenant_id == platform_admin_tenant_id,
                SkillMarketplacePayoutApproval.status == SkillMarketplacePayoutApprovalStatus.APPROVED,
            )
        )
    ).scalar_one_or_none()
    if approval is None:
        raise ConflictError("approved payout decision is required before execution")
    if approval.decided_by_user_id == executed_by_user_id:
        raise ConflictError("payout approver cannot be the same user who executes the payout")

    seller = (
        await db.execute(
            select(Tenant).where(
                Tenant.id == proposal.seller_tenant_id,
                Tenant.status == "active",
            )
        )
    ).scalar_one_or_none()
    if seller is None:
        raise ConflictError("seller tenant is not active")

    destination = (seller.settings or {}).get("marketplace_payout_destination")
    if not isinstance(destination, str) or not destination.strip() or len(destination.strip()) > 255:
        raise ConflictError("seller payout destination is not configured")

    provider = get_marketplace_payout_provider()
    idempotency_key = f"marketplace-payout:{proposal.id}"
    try:
        result = provider.execute(
            proposal_id=str(proposal.id),
            seller_tenant_id=str(proposal.seller_tenant_id),
            destination=destination.strip(),
            amount=str(proposal.amount),
            currency=proposal.currency,
            idempotency_key=idempotency_key,
        )
    except MarketplacePayoutProviderUnknown as exc:
        proposal.provider = provider.name
        proposal.execution_status = SkillMarketplacePayoutExecutionStatus.UNKNOWN
        settlement.payout_status = SkillMarketplacePayoutStatus.UNKNOWN
        metadata = dict(proposal.metadata_ or {})
        metadata.update(
            {
                "provider_execution": "unknown",
                "execution_idempotency_key": idempotency_key,
                "destination_configured": True,
                "unknown_reason": str(exc)[:500],
                "manual_reconciliation_required": True,
                "execution_authority_changed": False,
            }
        )
        proposal.metadata_ = metadata
        await db.flush()
        await audit_service.record(
            db,
            tenant_id=platform_admin_tenant_id,
            actor_id=executed_by_user_id,
            action="skill_marketplace_payout.execution_unknown",
            resource_type="skill_marketplace_payout_proposal",
            resource_id=str(proposal.id),
            metadata={
                "provider": provider.name,
                "idempotency_key": idempotency_key,
                "reason": str(exc)[:500],
                "manual_reconciliation_required": True,
                "settlement_id": str(settlement.id),
            },
        )
        return proposal
    except MarketplacePayoutProviderError as exc:
        raise ValidationAppError(str(exc)) from exc

    if not result.executed:
        raise ConflictError("payout provider did not confirm execution")

    proposal.provider = result.provider
    proposal.provider_payout_id = result.provider_payout_id
    proposal.execution_status = SkillMarketplacePayoutExecutionStatus.EXECUTED
    proposal.executed_at = datetime.now(timezone.utc)
    settlement.payout_status = SkillMarketplacePayoutStatus.EXECUTED

    metadata = dict(proposal.metadata_ or {})
    metadata.update(
        {
            "provider_execution": result.status,
            "execution_idempotency_key": idempotency_key,
            "destination_configured": True,
            "seller_payout": "executed",
            "execution_authority_changed": False,
        }
    )
    proposal.metadata_ = metadata
    await db.flush()

    await audit_service.record(
        db,
        tenant_id=platform_admin_tenant_id,
        actor_id=executed_by_user_id,
        action="skill_marketplace_payout.executed",
        resource_type="skill_marketplace_payout_proposal",
        resource_id=str(proposal.id),
        metadata={
            "seller_tenant_id": str(proposal.seller_tenant_id),
            "provider": result.provider,
            "provider_payout_id": result.provider_payout_id,
            "amount": str(proposal.amount),
            "currency": proposal.currency,
            "execution_idempotency_key": idempotency_key,
            "settlement_id": str(settlement.id),
            "execution_authority_changed": False,
        },
    )
    return proposal
