"""Governed AgentTemplate promotion using explicit evidence and approval."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationAppError
from app.models.agent_template import AgentTemplate, AgentTemplateStatus
from app.services.agent_governance import assert_publishable_with_evidence
from app.services.agent_promotion_evidence import agent_promotion_evidence_summary
from app.services.agent_template_service import publish_template


async def promote_agent_template(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    template_id: UUID,
    requested_by_user_id: UUID,
    approved_by_user_id: UUID,
) -> AgentTemplate:
    """Promote an evaluated candidate through an attributable human approval.

    Promotion is intentionally separate from evidence generation. The candidate
    must have comparable measured prior-version evidence and a passed governed
    evaluation. The requester and approver must be independently attributable.
    """
    if not requested_by_user_id or not approved_by_user_id:
        raise ValidationAppError("Promotion requester and approver are required")
    if requested_by_user_id == approved_by_user_id:
        raise ValidationAppError("Promotion requester and approver must be independent")

    evidence_rows = await agent_promotion_evidence_summary(
        db,
        tenant_id=tenant_id,
        agent_template_id=template_id,
        window_days=30,
    )
    evidence = next((item for item in evidence_rows if item.candidate_agent_template_id == template_id), None)
    if evidence is None:
        raise ConflictError("Promotion evidence is unavailable for the candidate AgentTemplate")
    if not evidence.comparable:
        raise ValidationAppError("Candidate AgentTemplate requires comparable prior-version evidence before promotion")

    template = await _load_template(db, tenant_id=tenant_id, template_id=template_id)
    if template.status not in {AgentTemplateStatus.DRAFT, AgentTemplateStatus.EVALUATING}:
        raise ConflictError("Agent template is not eligible for governed promotion")

    # Reuse the existing evaluation/policy gate; promotion must never create a
    # second authorization path around the Stage 8 governance substrate.
    await assert_publishable_with_evidence(db, tenant_id=tenant_id, template_id=template_id)
    return await publish_template(
        db,
        tenant_id=tenant_id,
        template_id=template_id,
        approved_by_user_id=approved_by_user_id,
    )


async def _load_template(db: AsyncSession, *, tenant_id: UUID, template_id: UUID) -> AgentTemplate:
    from sqlalchemy import select

    template = (
        await db.execute(
            select(AgentTemplate).where(
                AgentTemplate.id == template_id,
                AgentTemplate.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if template is None:
        raise ConflictError("Agent template is not available for promotion")
    return template
