"""Governed rollback planning for AgentInstance replacements."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_template import AgentTemplate, AgentTemplateStatus
from app.models.agent_workforce_proposal import AgentWorkforceProposal
from app.services.agent_workforce_replacement_service import create_replacement_proposal


async def create_rollback_proposal(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    requester_user_id: uuid.UUID,
    sponsor_user_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
    title: str,
    rationale: str,
    requested_name: str,
    configuration: dict | None = None,
) -> AgentWorkforceProposal:
    """Create a governed replacement proposal targeting the immediately prior template version.

    Rollback planning never mutates an active AgentInstance. The returned
    proposal must still pass the existing Board/CEO/provision/access-review
    and replacement cutover controls before execution authority changes.
    """
    if requester_user_id == sponsor_user_id:
        raise ValidationAppError("Requester and sponsor must be independently attributable")

    instance = (
        await db.execute(
            select(AgentInstance)
            .where(
                AgentInstance.id == agent_instance_id,
                AgentInstance.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if instance is None:
        raise NotFoundError("Agent instance not found")
    if instance.status == AgentInstanceStatus.RETIRED:
        raise ConflictError("A retired AgentInstance cannot be rolled back")
    if instance.agent_template_id is None:
        raise ValidationAppError("Rollback requires an AgentInstance bound to an AgentTemplate")

    current = (
        await db.execute(
            select(AgentTemplate).where(
                AgentTemplate.id == instance.agent_template_id,
                AgentTemplate.tenant_id == tenant_id,
            )
        )
    ).scalar_one_or_none()
    if current is None:
        raise NotFoundError("Current AgentTemplate not found for tenant")
    if current.status != AgentTemplateStatus.PUBLISHED:
        raise ConflictError("Rollback requires the current AgentTemplate to be published")

    previous = (
        await db.execute(
            select(AgentTemplate)
            .where(
                AgentTemplate.tenant_id == tenant_id,
                AgentTemplate.slug == current.slug,
                AgentTemplate.agent_definition_id == current.agent_definition_id,
                AgentTemplate.version < current.version,
                AgentTemplate.status == AgentTemplateStatus.PUBLISHED,
            )
            .order_by(AgentTemplate.version.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if previous is None:
        raise ConflictError("No previously published AgentTemplate version is available for rollback")

    proposal = await create_replacement_proposal(
        db,
        tenant_id=tenant_id,
        requester_user_id=requester_user_id,
        sponsor_user_id=sponsor_user_id,
        replacement_for_agent_instance_id=instance.id,
        agent_template_id=previous.id,
        title=title,
        rationale=rationale,
        requested_name=requested_name,
        risk_tier=previous.risk_tier,
        configuration={
            **(configuration or {}),
            "rollback": {
                "current_agent_template_id": str(current.id),
                "current_agent_template_version": current.version,
                "target_agent_template_id": str(previous.id),
                "target_agent_template_version": previous.version,
            },
        },
    )
    return proposal
