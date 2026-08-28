"""Resolve an AgentInstance to an executable runtime binding.

AgentDefinition and Employee are deliberately separate domain models. Until a
first-class binding exists between them, this resolver fails closed instead of
assuming their UUIDs are interchangeable.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance, AgentInstanceStatus


async def resolve_agent_definition(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
) -> tuple[AgentInstance, AgentDefinition]:
    """Resolve a tenant-scoped, enabled AgentInstance and its definition."""
    result = await db.execute(
        select(AgentInstance).where(
            AgentInstance.id == agent_instance_id,
            AgentInstance.tenant_id == tenant_id,
        )
    )
    instance = result.scalar_one_or_none()
    if instance is None:
        raise NotFoundError("Agent instance not found")
    if not instance.enabled or instance.status != AgentInstanceStatus.ENABLED:
        raise ConflictError("Agent instance is not accepting executions")

    result = await db.execute(
        select(AgentDefinition).where(
            AgentDefinition.id == instance.agent_definition_id,
            AgentDefinition.tenant_id == tenant_id,
        )
    )
    definition = result.scalar_one_or_none()
    if definition is None:
        raise NotFoundError("Agent definition not found")
    if not definition.enabled:
        raise ConflictError("Agent definition is disabled")

    return instance, definition


async def resolve_employee_version(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
):
    """Fail closed until an explicit AgentDefinition→EmployeeVersion binding exists.

    This intentionally does not compare UUIDs across the two domains. A future
    binding table/service must establish that relationship explicitly.
    """
    await resolve_agent_definition(
        db, tenant_id=tenant_id, agent_instance_id=agent_instance_id
    )
    raise ConflictError("Agent runtime binding is not configured")
