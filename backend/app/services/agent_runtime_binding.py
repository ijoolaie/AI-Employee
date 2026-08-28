"""Resolve an AgentInstance through an explicit tenant-scoped runtime binding."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.employee import EmployeeVersion


async def resolve_employee_version(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
) -> tuple[AgentInstance, AgentDefinition, EmployeeVersion]:
    """Resolve a tenant-scoped agent to its explicitly bound EmployeeVersion."""
    result = await db.execute(
        select(AgentInstance, AgentDefinition)
        .join(AgentDefinition, AgentDefinition.id == AgentInstance.agent_definition_id)
        .where(
            AgentInstance.id == agent_instance_id,
            AgentInstance.tenant_id == tenant_id,
            AgentDefinition.tenant_id == tenant_id,
        )
    )
    row = result.one_or_none()
    if row is None:
        raise NotFoundError("Agent instance not found")
    instance, definition = row
    if not instance.enabled or instance.status != AgentInstanceStatus.ENABLED:
        raise ConflictError("Agent instance is not accepting executions")
    if not definition.enabled:
        raise ConflictError("Agent definition is disabled")

    result = await db.execute(
        select(AgentRuntimeBinding, EmployeeVersion)
        .join(EmployeeVersion, EmployeeVersion.id == AgentRuntimeBinding.employee_version_id)
        .where(
            AgentRuntimeBinding.tenant_id == tenant_id,
            AgentRuntimeBinding.agent_definition_id == definition.id,
            AgentRuntimeBinding.is_active.is_(True),
        )
    )
    row = result.one_or_none()
    if row is None:
        raise ConflictError("Agent runtime binding is not configured")
    binding, version = row
    return instance, definition, version
