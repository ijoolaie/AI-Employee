"""Governed AgentInstance replacement and cutover workflow."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_workforce_proposal import AgentWorkforceProposal, AgentWorkforceProposalKind, AgentWorkforceProposalStatus
from app.services.agent_workforce_manager import get_agent_capacity
from app.services.agent_workforce_proposal_service import activate_provisioned_proposal, create_proposal
from app.services.audit_service import record


async def create_replacement_proposal(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    requester_user_id: uuid.UUID,
    sponsor_user_id: uuid.UUID,
    replacement_for_agent_instance_id: uuid.UUID,
    agent_template_id: uuid.UUID,
    title: str,
    rationale: str,
    requested_name: str,
    risk_tier: int,
    configuration: dict | None = None,
) -> AgentWorkforceProposal:
    predecessor = (
        await db.execute(
            select(AgentInstance)
            .where(
                AgentInstance.id == replacement_for_agent_instance_id,
                AgentInstance.tenant_id == tenant_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if predecessor is None:
        raise NotFoundError("Agent instance to replace not found")
    if predecessor.status == AgentInstanceStatus.RETIRED:
        raise ConflictError("A retired AgentInstance cannot be replaced")

    proposal = await create_proposal(
        db,
        tenant_id=tenant_id,
        requester_user_id=requester_user_id,
        title=title,
        rationale=rationale,
        requested_name=requested_name,
        sponsor_user_id=sponsor_user_id,
        agent_template_id=agent_template_id,
        risk_tier=risk_tier,
        configuration={
            **(configuration or {}),
            "replacement": {
                "predecessor_agent_instance_id": str(predecessor.id),
                "predecessor_agent_definition_id": str(predecessor.agent_definition_id),
                "predecessor_agent_template_id": str(predecessor.agent_template_id) if predecessor.agent_template_id else None,
            },
        },
    )
    proposal.kind = AgentWorkforceProposalKind.REPLACEMENT
    proposal.replacement_for_agent_instance_id = predecessor.id
    await db.flush()
    await record(
        db,
        action="agent_workforce.replacement.proposal_submitted",
        actor_id=requester_user_id,
        tenant_id=tenant_id,
        resource_type="agent_workforce_proposal",
        resource_id=proposal.id,
        metadata={
            "predecessor_agent_instance_id": str(predecessor.id),
            "replacement_template_id": str(agent_template_id),
            "risk_tier": risk_tier,
        },
    )
    return proposal


async def prepare_replacement_cutover(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    proposal_id: uuid.UUID,
    requested_by_user_id: uuid.UUID,
) -> AgentWorkforceProposal:
    proposal = await _locked_proposal(db, tenant_id, proposal_id)
    if proposal.kind != AgentWorkforceProposalKind.REPLACEMENT:
        raise ConflictError("Only replacement workforce proposals can enter replacement cutover")
    if proposal.status != AgentWorkforceProposalStatus.PROVISIONED:
        raise ConflictError("Replacement cutover requires a provisioned replacement")
    if requested_by_user_id in {
        proposal.requester_user_id,
        proposal.sponsor_user_id,
        proposal.board_reviewed_by,
        proposal.ceo_approved_by,
    }:
        raise ValidationAppError("Replacement cutover operator must be independent from proposal authorities")
    if not proposal.replacement_for_agent_instance_id:
        raise ValidationAppError("Replacement proposal has no predecessor AgentInstance")

    predecessor = (
        await db.execute(
            select(AgentInstance)
            .where(
                AgentInstance.id == proposal.replacement_for_agent_instance_id,
                AgentInstance.tenant_id == tenant_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if predecessor is None:
        raise NotFoundError("Replacement predecessor AgentInstance not found")
    if predecessor.status == AgentInstanceStatus.RETIRED:
        raise ConflictError("Replacement predecessor is already retired")
    if predecessor.status == AgentInstanceStatus.ENABLED:
        predecessor.status = AgentInstanceStatus.DRAINING
        predecessor.enabled = True
    elif predecessor.status != AgentInstanceStatus.DRAINING:
        raise ConflictError("Replacement predecessor must be enabled or draining before cutover")
    await db.flush()
    await record(
        db,
        action="agent_workforce.replacement.cutover_prepared",
        actor_id=requested_by_user_id,
        tenant_id=tenant_id,
        resource_type="agent_workforce_proposal",
        resource_id=proposal.id,
        metadata={"predecessor_agent_instance_id": str(predecessor.id)},
    )
    return proposal


async def cutover_replacement(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    proposal_id: uuid.UUID,
    cutover_by_user_id: uuid.UUID,
) -> AgentWorkforceProposal:
    proposal = await _locked_proposal(db, tenant_id, proposal_id)
    if proposal.kind != AgentWorkforceProposalKind.REPLACEMENT:
        raise ConflictError("Only replacement workforce proposals can complete replacement cutover")
    if proposal.status != AgentWorkforceProposalStatus.PROVISIONED:
        raise ConflictError("Replacement cutover requires a provisioned replacement")
    if cutover_by_user_id in {
        proposal.requester_user_id,
        proposal.sponsor_user_id,
        proposal.board_reviewed_by,
        proposal.ceo_approved_by,
    }:
        raise ValidationAppError("Replacement cutover operator must be independent from proposal authorities")
    if not proposal.provisioned_agent_instance_id or not proposal.replacement_for_agent_instance_id:
        raise ValidationAppError("Replacement proposal is missing predecessor or replacement AgentInstance")

    predecessor = (
        await db.execute(
            select(AgentInstance)
            .where(
                AgentInstance.id == proposal.replacement_for_agent_instance_id,
                AgentInstance.tenant_id == tenant_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if predecessor is None:
        raise NotFoundError("Replacement predecessor AgentInstance not found")
    if predecessor.status != AgentInstanceStatus.DRAINING:
        raise ConflictError("Replacement predecessor must be draining before cutover")

    capacity = await get_agent_capacity(
        db,
        tenant_id=tenant_id,
        agent_instance_id=predecessor.id,
        for_update=True,
    )
    if int(capacity["active_work_items"]) != 0:
        raise ConflictError("Replacement predecessor still has active WorkItems")

    # This re-check performs the full CEO/access-review/fingerprint validation
    # before granting execution authority to the replacement. Any later failure
    # rolls the transaction back, so the predecessor remains draining.
    await activate_provisioned_proposal(
        db,
        tenant_id=tenant_id,
        proposal_id=proposal.id,
        activated_by_user_id=cutover_by_user_id,
    )

    replacement = (
        await db.execute(
            select(AgentInstance)
            .where(
                AgentInstance.id == proposal.provisioned_agent_instance_id,
                AgentInstance.tenant_id == tenant_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if replacement is None:
        raise NotFoundError("Replacement AgentInstance not found")
    if replacement.status != AgentInstanceStatus.ENABLED or not replacement.enabled:
        raise ConflictError("Replacement AgentInstance did not reach enabled state")

    predecessor.status = AgentInstanceStatus.RETIRED
    predecessor.enabled = False
    now = datetime.now(timezone.utc)
    proposal.replacement_cutover_at = now
    proposal.replacement_retired_at = now
    await db.flush()
    await record(
        db,
        action="agent_workforce.replacement.cutover_completed",
        actor_id=cutover_by_user_id,
        tenant_id=tenant_id,
        resource_type="agent_workforce_proposal",
        resource_id=proposal.id,
        metadata={
            "predecessor_agent_instance_id": str(predecessor.id),
            "replacement_agent_instance_id": str(replacement.id),
            "replacement_agent_template_id": str(replacement.agent_template_id) if replacement.agent_template_id else None,
            "cutover_at": now.isoformat(),
        },
    )
    return proposal


async def _locked_proposal(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    proposal_id: uuid.UUID,
) -> AgentWorkforceProposal:
    result = await db.execute(
        select(AgentWorkforceProposal)
        .where(
            AgentWorkforceProposal.id == proposal_id,
            AgentWorkforceProposal.tenant_id == tenant_id,
        )
        .with_for_update()
    )
    proposal = result.scalar_one_or_none()
    if proposal is None:
        raise NotFoundError("Workforce proposal not found")
    return proposal
