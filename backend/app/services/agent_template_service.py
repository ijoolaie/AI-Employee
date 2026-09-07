"""Governed AgentTemplate lifecycle and tenant-scoped AgentInstance provisioning."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, ValidationAppError
from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_template import AgentTemplate, AgentTemplateStatus


async def create_template(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_definition_id: uuid.UUID,
    slug: str,
    name: str,
    description: str | None = None,
    version: int = 1,
    risk_tier: int = 0,
    capability_contract: dict | None = None,
    permission_policy: dict | None = None,
    approval_policy: dict | None = None,
    evaluation_policy: dict | None = None,
    install_policy: dict | None = None,
    is_system_template: bool = False,
) -> AgentTemplate:
    definition = (await db.execute(select(AgentDefinition).where(
        AgentDefinition.id == agent_definition_id,
        AgentDefinition.tenant_id == tenant_id,
        AgentDefinition.enabled.is_(True),
    ))).scalar_one_or_none()
    if definition is None:
        raise NotFoundError("Agent definition not found for tenant")
    if not 0 <= risk_tier <= 4:
        raise ValidationAppError("risk_tier must be between 0 and 4")
    if version < 1:
        raise ValidationAppError("version must be at least 1")

    duplicate = (await db.execute(select(AgentTemplate).where(
        AgentTemplate.tenant_id == tenant_id,
        AgentTemplate.slug == slug,
        AgentTemplate.version == version,
    ))).scalar_one_or_none()
    if duplicate is not None:
        raise ConflictError("Agent template version already exists")

    template = AgentTemplate(
        tenant_id=tenant_id,
        agent_definition_id=definition.id,
        slug=slug,
        name=name,
        description=description,
        version=version,
        risk_tier=risk_tier,
        capability_contract=capability_contract or {},
        permission_policy=permission_policy or {},
        approval_policy=approval_policy or {},
        evaluation_policy=evaluation_policy or {},
        install_policy=install_policy or {},
        is_system_template=is_system_template,
        status=AgentTemplateStatus.DRAFT,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)
    return template


async def publish_template(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
    approved_by_user_id: uuid.UUID,
) -> AgentTemplate:
    template = (await db.execute(select(AgentTemplate).where(
        AgentTemplate.id == template_id,
        AgentTemplate.tenant_id == tenant_id,
    ))).scalar_one_or_none()
    if template is None:
        raise NotFoundError("Agent template not found")
    if template.status not in {AgentTemplateStatus.DRAFT, AgentTemplateStatus.EVALUATING}:
        raise ConflictError("Agent template is not publishable from its current state")
    if not template.evaluation_policy.get("passed", False):
        raise ValidationAppError("Agent template evaluation must pass before publication")
    if not approved_by_user_id:
        raise ValidationAppError("CEO or designated approver is required for publication")

    template.status = AgentTemplateStatus.PUBLISHED
    template.published_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(template)
    return template


async def provision_instance(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    template_id: uuid.UUID,
    name: str,
    sponsor_user_id: uuid.UUID,
    approved_by_user_id: uuid.UUID,
    configuration: dict | None = None,
) -> AgentInstance:
    template = (await db.execute(select(AgentTemplate).where(
        AgentTemplate.id == template_id,
        AgentTemplate.tenant_id == tenant_id,
        AgentTemplate.status == AgentTemplateStatus.PUBLISHED,
    ))).scalar_one_or_none()
    if template is None:
        raise NotFoundError("Published agent template not found")
    if not sponsor_user_id or not approved_by_user_id:
        raise ValidationAppError("Sponsor and CEO/designated approver are required")

    policy = template.install_policy or {}
    if policy.get("requires_ceo_approval", True) and sponsor_user_id == approved_by_user_id:
        raise ValidationAppError("Sponsor and approver must be independently attributable for governed installation")

    instance = AgentInstance(
        tenant_id=tenant_id,
        agent_definition_id=template.agent_definition_id,
        agent_template_id=template.id,
        sponsor_user_id=sponsor_user_id,
        name=name,
        configuration=configuration or {},
        permission_policy=template.permission_policy or {},
        approval_policy=template.approval_policy or {},
        risk_tier=template.risk_tier,
        status=AgentInstanceStatus.ENABLED,
        enabled=True,
    )
    db.add(instance)
    await db.flush()
    await db.refresh(instance)
    return instance


_ALLOWED_LIFECYCLE_TRANSITIONS: dict[AgentInstanceStatus, set[AgentInstanceStatus]] = {
    AgentInstanceStatus.ENABLED: {AgentInstanceStatus.DRAINING, AgentInstanceStatus.SUSPENDED, AgentInstanceStatus.RETIRED},
    AgentInstanceStatus.DRAINING: {AgentInstanceStatus.ENABLED, AgentInstanceStatus.SUSPENDED, AgentInstanceStatus.RETIRED},
    AgentInstanceStatus.SUSPENDED: {AgentInstanceStatus.ENABLED, AgentInstanceStatus.RETIRED},
    AgentInstanceStatus.DISABLED: {AgentInstanceStatus.ENABLED, AgentInstanceStatus.RETIRED},
    AgentInstanceStatus.RETIRED: set(),
}


async def transition_instance(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    instance_id: uuid.UUID,
    target_status: AgentInstanceStatus,
    requested_by_user_id: uuid.UUID,
    approved_by_user_id: uuid.UUID,
) -> AgentInstance:
    instance = (await db.execute(select(AgentInstance).where(
        AgentInstance.id == instance_id,
        AgentInstance.tenant_id == tenant_id,
    ))).scalar_one_or_none()
    if instance is None:
        raise NotFoundError("Agent instance not found")
    if target_status == instance.status:
        return instance
    if target_status not in _ALLOWED_LIFECYCLE_TRANSITIONS.get(instance.status, set()):
        raise ConflictError(f"Invalid agent instance lifecycle transition: {instance.status.value} -> {target_status.value}")
    if not requested_by_user_id or not approved_by_user_id:
        raise ValidationAppError("Lifecycle requester and approver are required")

    approval_policy = instance.approval_policy or {}
    requires_approval = bool(approval_policy.get("requires_ceo_approval", False)) or instance.risk_tier >= 3 or target_status in {
        AgentInstanceStatus.SUSPENDED,
        AgentInstanceStatus.RETIRED,
    }
    if requires_approval and requested_by_user_id == approved_by_user_id:
        raise ValidationAppError("Requester and approver must be independently attributable for governed lifecycle changes")

    instance.status = target_status
    instance.enabled = target_status in {AgentInstanceStatus.ENABLED, AgentInstanceStatus.DRAINING}
    if target_status == AgentInstanceStatus.RETIRED:
        instance.enabled = False
    await db.flush()
    await db.refresh(instance)
    return instance
