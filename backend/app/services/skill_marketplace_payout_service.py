"""Platform-admin marketplace payout proposals and governed provider execution."""
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
from app.models.tool_approval import ToolApprovalRequest
from app.models.skill_marketplace_settlement import (
    SkillMarketplacePayoutStatus,
    SkillMarketplaceSettlementStatus,
    SkillMarketplaceSettlement,
)
from app.models.tenant import Tenant
from app.models.user import User
from app.services import audit_service
from app.services.skill_marketplace_payout_provider import (
    MarketplacePayoutRequest,
    MarketplacePayoutStatus,
    get_marketplace_payout_provider,
)


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


async def list_payout_execution_evidence(
    db: AsyncSession,
    *,
    platform_admin_tenant_id: uuid.UUID,
    execution_status: SkillMarketplacePayoutExecutionStatus | None = None,
    seller_tenant_id: uuid.UUID | None = None,
) -> list[SkillMarketplacePayoutProposal]:
    """Return read-only durable payout execution evidence for platform admins."""
    stmt = select(SkillMarketplacePayoutProposal).where(
        SkillMarketplacePayoutProposal.platform_admin_tenant_id == platform_admin_tenant_id
    )
    if execution_status is not None:
        stmt = stmt.where(SkillMarketplacePayoutProposal.execution_status == execution_status)
    if seller_tenant_id is not None:
        stmt = stmt.where(SkillMarketplacePayoutProposal.seller_tenant_id == seller_tenant_id)
    stmt = stmt.order_by(SkillMarketplacePayoutProposal.updated_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def execute_payout_proposal(
    db: AsyncSession,
    *,
    proposal_id: uuid.UUID,
    platform_admin_tenant_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    approval_granted: bool,
    approval_request_id: uuid.UUID | None,
) -> SkillMarketplacePayoutProposal:
    """Execute one approved payout proposal through the named provider boundary.

    This operation is intentionally fail-closed: it requires explicit approval,
    an active vendor platform-admin actor, an immutable destination snapshot,
    and a durable idempotency key. The operator-selected provider is resolved
    from configuration; runtime arguments cannot select it.
    """
    if not approval_granted or approval_request_id is None:
        raise ValidationAppError("marketplace payout execution requires a durable explicit approval")

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
        raise ValidationAppError("payout execution requires an active vendor platform-admin tenant")

    admin_user = (
        await db.execute(
            select(User).where(
                User.id == actor_user_id,
                User.tenant_id == platform_admin_tenant_id,
                User.is_active.is_(True),
                User.is_platform_admin.is_(True),
            )
        )
    ).scalar_one_or_none()
    if admin_user is None:
        raise ValidationAppError("payout execution requires an active platform administrator")

    approval_result = await db.execute(
        select(ToolApprovalRequest).where(
            ToolApprovalRequest.id == approval_request_id,
            ToolApprovalRequest.tenant_id == platform_admin_tenant_id,
        ).with_for_update()
    )
    approval = approval_result.scalar_one_or_none()
    if approval is None:
        raise ValidationAppError("payout execution approval request was not found")
    if approval.tool_name != "marketplace_execute_payout":
        raise ValidationAppError("approval request is bound to a different tool")
    if approval.status not in {"approved", "consumed"} or approval.decided_by is None or approval.decided_at is None:
        raise ValidationAppError("payout execution approval was not explicitly decided")
    if approval.arguments != {"proposal_id": str(proposal_id)}:
        raise ValidationAppError("payout execution approval arguments do not match the proposal")
    if approval.status == "approved":
        approval.status = "consumed"
        await db.flush()

    result = await db.execute(
        select(SkillMarketplacePayoutProposal)
        .where(
            SkillMarketplacePayoutProposal.id == proposal_id,
            SkillMarketplacePayoutProposal.platform_admin_tenant_id == platform_admin_tenant_id,
        )
        .with_for_update()
    )
    proposal = result.scalar_one_or_none()
    if proposal is None:
        raise NotFoundError("marketplace payout proposal was not found")

    if proposal.destination_id is None or not proposal.destination_provider or not proposal.destination_ref:
        raise ValidationAppError("payout proposal has no immutable seller destination snapshot")

    if proposal.execution_status is SkillMarketplacePayoutExecutionStatus.ACCEPTED:
        return proposal
    if proposal.execution_status is SkillMarketplacePayoutExecutionStatus.UNKNOWN:
        raise ConflictError("payout execution is UNKNOWN and requires manual reconciliation")
    if proposal.execution_status is SkillMarketplacePayoutExecutionStatus.PENDING:
        raise ConflictError("payout execution is already pending")
    if proposal.execution_status is SkillMarketplacePayoutExecutionStatus.FAILED and not proposal.retryable:
        raise ConflictError("non-retryable payout execution failure requires a new governed decision")
    if proposal.status is SkillMarketplacePayoutProposalStatus.CANCELLED:
        raise ConflictError("cancelled payout proposal cannot be executed")

    if not proposal.idempotency_key:
        proposal.idempotency_key = f"marketplace-payout-{proposal.id}"

    proposal.execution_status = SkillMarketplacePayoutExecutionStatus.PENDING
    proposal.metadata_ = {
        **(proposal.metadata_ or {}),
        "seller_payout": "pending",
        "provider_execution": "pending",
        "approval_required": True,
        "approval_granted": True,
        "destination": "bound_snapshot",
        "execution_authority_changed": False,
    }
    await db.flush()

    provider = get_marketplace_payout_provider()
    payout_request = MarketplacePayoutRequest(
        proposal_id=proposal.id,
        settlement_id=proposal.settlement_id,
        seller_tenant_id=proposal.seller_tenant_id,
        amount=Decimal(str(proposal.amount)),
        currency=proposal.currency,
        destination_ref=proposal.destination_ref,
        idempotency_key=proposal.idempotency_key,
    )

    try:
        provider_result = await provider.create_payout(payout_request)
    except Exception as exc:
        proposal.execution_status = SkillMarketplacePayoutExecutionStatus.UNKNOWN
        proposal.executed = False
        proposal.external_execution = False
        proposal.failure_code = "provider_execution_unknown"
        proposal.retryable = False
        proposal.metadata_ = {
            **(proposal.metadata_ or {}),
            "seller_payout": "unknown",
            "provider_execution": "unknown",
            "provider_exception": type(exc).__name__,
            "reconciliation_required": True,
        }
        await audit_service.record(
            db,
            tenant_id=platform_admin_tenant_id,
            actor_id=actor_user_id,
            action="skill_marketplace_payout.execution_unknown",
            resource_type="skill_marketplace_payout_proposal",
            resource_id=str(proposal.id),
            metadata={
                "provider": getattr(provider, "name", "unknown"),
                "execution_status": proposal.execution_status.value,
                "reconciliation_required": True,
            },
        )
        await db.flush()
        return proposal

    proposal.provider = provider_result.provider
    proposal.provider_payout_id = provider_result.provider_payout_id
    proposal.provider_event_id = provider_result.provider_event_id
    proposal.failure_code = provider_result.failure_code
    proposal.retryable = provider_result.retryable
    proposal.executed = provider_result.executed
    proposal.external_execution = provider_result.external_execution

    if provider_result.status is MarketplacePayoutStatus.ACCEPTED:
        proposal.execution_status = SkillMarketplacePayoutExecutionStatus.ACCEPTED
        seller_payout_state = "accepted"
    elif provider_result.status is MarketplacePayoutStatus.FAILED:
        proposal.execution_status = SkillMarketplacePayoutExecutionStatus.FAILED
        seller_payout_state = "failed"
    elif provider_result.status is MarketplacePayoutStatus.UNKNOWN:
        proposal.execution_status = SkillMarketplacePayoutExecutionStatus.UNKNOWN
        seller_payout_state = "unknown"
    else:
        proposal.execution_status = SkillMarketplacePayoutExecutionStatus.FAILED
        seller_payout_state = "not_configured"

    proposal.metadata_ = {
        **(proposal.metadata_ or {}),
        "seller_payout": seller_payout_state,
        "provider_execution": provider_result.provider_execution,
        "approval_required": True,
        "approval_granted": True,
        "destination": "bound_snapshot",
        "execution_authority_changed": False,
        "reconciliation_required": proposal.execution_status is SkillMarketplacePayoutExecutionStatus.UNKNOWN,
    }
    await audit_service.record(
        db,
        tenant_id=platform_admin_tenant_id,
        actor_id=actor_user_id,
        action="skill_marketplace_payout.executed",
        resource_type="skill_marketplace_payout_proposal",
        resource_id=str(proposal.id),
        metadata={
            "provider": provider_result.provider,
            "execution_status": proposal.execution_status.value,
            "executed": provider_result.executed,
            "external_execution": provider_result.external_execution,
            "provider_payout_id": provider_result.provider_payout_id,
            "provider_event_id": provider_result.provider_event_id,
            "reconciliation_required": proposal.execution_status is SkillMarketplacePayoutExecutionStatus.UNKNOWN,
        },
    )
    await db.flush()
    return proposal
