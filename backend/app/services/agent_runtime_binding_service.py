"""Application service for safely creating and resolving Agent runtime bindings."""
from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.agent_definition import AgentDefinition
from app.models.agent_runtime_binding import AgentRuntimeBinding
from app.models.employee import EmployeeVersion


async def bind_employee_version(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_definition_id: uuid.UUID,
    employee_version_id: uuid.UUID,
) -> AgentRuntimeBinding:
    definition = (await db.execute(select(AgentDefinition).where(
        AgentDefinition.id == agent_definition_id,
        AgentDefinition.tenant_id == tenant_id,
        AgentDefinition.enabled.is_(True),
    ))).scalar_one_or_none()
    if definition is None:
        raise NotFoundError("Agent definition not found")

    version = (await db.execute(select(EmployeeVersion).where(
        EmployeeVersion.id == employee_version_id,
    ))).scalar_one_or_none()
    if version is None:
        raise NotFoundError("Employee version not found")

    employee_tenant = getattr(version.employee, "tenant_id", None) if version.employee is not None else None
    if employee_tenant != tenant_id:
        raise ConflictError("Employee version belongs to a different tenant")

    existing = (await db.execute(select(AgentRuntimeBinding).where(
        AgentRuntimeBinding.tenant_id == tenant_id,
        AgentRuntimeBinding.agent_definition_id == agent_definition_id,
    ))).scalar_one_or_none()
    if existing is not None:
        if existing.employee_version_id == employee_version_id and existing.is_active:
            return existing
        raise ConflictError("Agent definition already has a runtime binding")

    binding = AgentRuntimeBinding(
        tenant_id=tenant_id,
        agent_definition_id=agent_definition_id,
        employee_version_id=employee_version_id,
        is_active=True,
    )
    db.add(binding)
    await db.flush()
    await db.refresh(binding)
    return binding
