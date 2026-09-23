"""Controlled materialization of first-party AI workforce AgentTemplates.

This module bridges the declarative workforce role catalog to the governed
AgentTemplate lifecycle. It creates a DRAFT only; evaluation, publication,
provisioning, access review, and activation remain separate governed steps.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_template import AgentTemplate
from app.services.agent_template_service import create_template
from app.services.ai_workforce_roles import (
    get_workforce_role_template,
    workforce_template_capability_contract,
)


async def create_first_party_workforce_template(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_definition_id: uuid.UUID,
    role_code: str,
    version: int,
    risk_tier: int,
    permission_policy: dict,
    approval_policy: dict,
    evaluation_policy: dict,
    install_policy: dict,
    name: str | None = None,
    description: str | None = None,
) -> AgentTemplate:
    """Materialize one catalog role as a governed, unpublished AgentTemplate.

    The role capability contract is always sourced from the current catalog;
    callers cannot supply or override a workforce capability snapshot.
    """

    role_template = get_workforce_role_template(role_code)
    capability_contract = workforce_template_capability_contract(role_code)

    return await create_template(
        db,
        tenant_id=tenant_id,
        agent_definition_id=agent_definition_id,
        slug=role_template.slug,
        name=name or role_template.name,
        description=description or role_template.description,
        version=version,
        risk_tier=risk_tier,
        capability_contract=capability_contract,
        permission_policy=permission_policy,
        approval_policy=approval_policy,
        evaluation_policy=evaluation_policy,
        install_policy=install_policy,
        is_system_template=True,
    )
