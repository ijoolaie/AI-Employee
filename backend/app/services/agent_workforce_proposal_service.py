"""Business rules for Need -> Proposal -> Board -> CEO -> AgentInstance."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.agent_access_review import AgentAccessReview, AgentAccessReviewDecision
from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_identity import AgentIdentity
from app.models.agent_template import AgentTemplate
from app.models.agent_workforce_proposal import AgentWorkforceProposal, AgentWorkforceProposalStatus
from app.services.agent_template_service import provision_instance
from app.services.audit_service import record


async def create_proposal(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    requester_user_id: uuid.UUID,
    title: str,
    rationale: str,
    requested_name: str,
    sponsor_user_id: uuid.UUID,
    agent_template_id: uuid.UUID | None = None,
    agent_definition_id: uuid.UUID | None = None,
    risk_tier: int = 0,
    configuration: dict | None = None,
) -> AgentWorkforceProposal:
    if not 0 <= risk_tier <= 4:
        raise ValidationAppError("risk_tier must be between 0 and 4")
    if requester_user_id == sponsor_user_id:
        raise ValidationAppError("Requester and sponsor must be independently attributable")
    if not agent_template_id and not agent_definition_id:
        raise ValidationAppError("A template or agent definition is required")

    if agent_template_id:
        template = (await db.execute(select(AgentTemplate).where(
            AgentTemplate.id == agent_template_id,
            AgentTemplate.tenant_id == tenant_id,
        ))).scalar_one_or_none()
        if template is None:
            raise NotFoundError("Agent template not found for tenant")
        if template.status.value != "published":
            raise ValidationAppError("Workforce proposals can only install published agent templates")
        if risk_tier != template.risk_tier:
            raise ValidationAppError("Proposal risk_tier must match the selected agent template")
        agent_definition_id = template.agent_definition_id
    else:
        definition = (await db.execute(select(AgentDefinition).where(
            AgentDefinition.id == agent_definition_id,
            AgentDefinition.tenant_id == tenant_id,
            AgentDefinition.enabled.is_(True),
        ))).scalar_one_or_none()
        if definition is None:
            raise NotFoundError("Agent definition not found for tenant")
        raise ValidationAppError("New role provisioning requires an evaluated and published AgentTemplate")

    proposal = AgentWorkforceProposal(
        tenant_id=tenant_id,
        agent_template_id=agent_template_id,
        agent_definition_id=agent_definition_id,
        title=title,
        rationale=rationale,
        requested_name=requested_name,
        requester_user_id=requester_user_id,
        sponsor_user_id=sponsor_user_id,
        risk_tier=risk_tier,
        configuration=configuration or {},
        status=AgentWorkforceProposalStatus.SUBMITTED,
    )
    db.add(proposal)
    await db.flush()
    await db.refresh(proposal)
    await record(db, action="agent_workforce.proposal.submitted", actor_id=requester_user_id, tenant_id=tenant_id, resource_type="agent_workforce_proposal", resource_id=proposal.id, metadata={"template_id": str(agent_template_id) if agent_template_id else None, "risk_tier": risk_tier})
    return proposal


async def board_decide(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    proposal_id: uuid.UUID,
    reviewer_user_id: uuid.UUID,
    approve: bool,
    reason: str | None = None,
) -> AgentWorkforceProposal:
    proposal = await _get_locked(db, tenant_id, proposal_id)
    if proposal.status != AgentWorkforceProposalStatus.SUBMITTED:
        raise ConflictError("Board decision requires a submitted workforce proposal")
    if reviewer_user_id in {proposal.requester_user_id, proposal.sponsor_user_id}:
        raise ValidationAppError("Board reviewer must be independent from requester and sponsor")
    proposal.board_reviewed_by = reviewer_user_id
    proposal.board_decision_reason = reason
    proposal.status = AgentWorkforceProposalStatus.BOARD_APPROVED if approve else AgentWorkforceProposalStatus.BOARD_REJECTED
    await db.flush()
    await record(db, action="agent_workforce.proposal.board_decided", actor_id=reviewer_user_id, tenant_id=tenant_id, resource_type="agent_workforce_proposal", resource_id=proposal.id, metadata={"decision": proposal.status.value, "reason": reason})
    return proposal


async def ceo_decide(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    proposal_id: uuid.UUID,
    approver_user_id: uuid.UUID,
    approve: bool,
    reason: str | None = None,
) -> AgentWorkforceProposal:
    proposal = await _get_locked(db, tenant_id, proposal_id)
    if proposal.status != AgentWorkforceProposalStatus.BOARD_APPROVED:
        raise ConflictError("CEO decision requires prior Board approval")
    if approver_user_id in {proposal.requester_user_id, proposal.sponsor_user_id, proposal.board_reviewed_by}:
        raise ValidationAppError("CEO approver must be independent from requester, sponsor and Board reviewer")
    proposal.ceo_approved_by = approver_user_id if approve else None
    proposal.ceo_decision_reason = reason
    proposal.status = AgentWorkforceProposalStatus.CEO_APPROVED if approve else AgentWorkforceProposalStatus.CEO_REJECTED
    await db.flush()
    await record(db, action="agent_workforce.proposal.ceo_decided", actor_id=approver_user_id, tenant_id=tenant_id, resource_type="agent_workforce_proposal", resource_id=proposal.id, metadata={"decision": proposal.status.value, "reason": reason})
    return proposal


async def provision_approved_proposal(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    proposal_id: uuid.UUID,
) -> AgentWorkforceProposal:
    proposal = await _get_locked(db, tenant_id, proposal_id)
    if proposal.status != AgentWorkforceProposalStatus.CEO_APPROVED:
        raise ConflictError("Only CEO-approved workforce proposals may be provisioned")
    if not proposal.agent_template_id or not proposal.ceo_approved_by:
        raise ValidationAppError("CEO-approved proposal is missing provisioning authority or template")

    instance = await provision_instance(
        db,
        tenant_id=tenant_id,
        template_id=proposal.agent_template_id,
        name=proposal.requested_name,
        sponsor_user_id=proposal.sponsor_user_id,
        approved_by_user_id=proposal.ceo_approved_by,
        configuration=proposal.configuration,
        activate=False,
    )
    proposal.provisioned_agent_instance_id = instance.id
    proposal.status = AgentWorkforceProposalStatus.PROVISIONED
    await db.flush()
    await record(db, action="agent_workforce.proposal.provisioned", actor_id=proposal.ceo_approved_by, tenant_id=tenant_id, resource_type="agent_workforce_proposal", resource_id=proposal.id, metadata={"agent_instance_id": str(instance.id), "activation": "blocked_pending_access_review"})
    return proposal


async def activate_provisioned_proposal(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    proposal_id: uuid.UUID,
    activated_by_user_id: uuid.UUID,
) -> AgentWorkforceProposal:
    proposal = await _get_locked(db, tenant_id, proposal_id)
    if proposal.status != AgentWorkforceProposalStatus.PROVISIONED:
        raise ConflictError("Only provisioned workforce proposals may be activated")
    if not proposal.provisioned_agent_instance_id:
        raise ValidationAppError("Provisioned workforce proposal has no AgentInstance")
    if activated_by_user_id in {proposal.requester_user_id, proposal.sponsor_user_id, proposal.board_reviewed_by, proposal.ceo_approved_by}:
        raise ValidationAppError("Activation reviewer must be independent from proposal authorities")

    instance = (await db.execute(select(AgentInstance).where(
        AgentInstance.id == proposal.provisioned_agent_instance_id,
        AgentInstance.tenant_id == tenant_id,
    ).with_for_update())).scalar_one_or_none()
    identity = (await db.execute(select(AgentIdentity).where(
        AgentIdentity.agent_instance_id == proposal.provisioned_agent_instance_id,
        AgentIdentity.tenant_id == tenant_id,
    ))).scalar_one_or_none()
    if instance is None or identity is None:
        raise NotFoundError("Provisioned AgentInstance identity state not found")
    if instance.status != AgentInstanceStatus.SUSPENDED:
        raise ConflictError("AgentInstance is not awaiting access-review activation")
    review = (await db.execute(select(AgentAccessReview).where(
        AgentAccessReview.agent_identity_id == identity.id,
        AgentAccessReview.tenant_id == tenant_id,
        AgentAccessReview.decision == AgentAccessReviewDecision.APPROVED,
    ).order_by(AgentAccessReview.reviewed_at.desc()).limit(1))).scalar_one_or_none()
    if review is None:
        raise ValidationAppError("An approved access review is required before activation")

    instance.status = AgentInstanceStatus.ENABLED
    instance.enabled = True
    await db.flush()
    await record(db, action="agent_workforce.proposal.activated", actor_id=activated_by_user_id, tenant_id=tenant_id, resource_type="agent_workforce_proposal", resource_id=proposal.id, metadata={"agent_instance_id": str(instance.id), "access_review_id": str(review.id)})
    return proposal


async def _get_locked(db: AsyncSession, tenant_id: uuid.UUID, proposal_id: uuid.UUID) -> AgentWorkforceProposal:
    result = await db.execute(select(AgentWorkforceProposal).where(
        AgentWorkforceProposal.id == proposal_id,
        AgentWorkforceProposal.tenant_id == tenant_id,
    ).with_for_update())
    proposal = result.scalar_one_or_none()
    if proposal is None:
        raise NotFoundError("Workforce proposal not found")
    return proposal
