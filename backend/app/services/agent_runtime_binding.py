"""Resolve a tenant-scoped AgentInstance to an immutable Employee runtime version."""
from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.agent_instance import AgentInstance
from app.models.employee import Employee, EmployeeVersion


async def resolve_employee_version(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    agent_instance_id: uuid.UUID,
) -> tuple[AgentInstance, Employee, EmployeeVersion]:
    """Resolve an enabled agent to a concrete EmployeeVersion.

    The binding is deliberately resolved at dispatch time and the selected
    version is returned to the caller so RunService can persist that exact
    version. No cross-tenant lookup is permitted.
    """
    result = await db.execute(
        select(AgentInstance).where(
            AgentInstance.id == agent_instance_id,
            AgentInstance.tenant_id == tenant_id,
        )
    )
    instance = result.scalar_one_or_none()
    if instance is None:
        raise NotFoundError("Agent instance not found")
    if not instance.enabled:
        raise ConflictError("Agent instance is disabled")
    if instance.status != "ENABLED":
        raise ConflictError(f"Agent instance is not accepting executions: {instance.status}")

    result = await db.execute(
        select(Employee).where(
            Employee.id == instance.agent_definition_id,
            Employee.tenant_id == tenant_id,
        )
    )
    employee = result.scalar_one_or_none()
    if employee is None:
        raise NotFoundError("Agent runtime binding not found")

    result = await db.execute(
        select(EmployeeVersion)
        .where(
            EmployeeVersion.employee_id == employee.id,
            EmployeeVersion.is_current.is_(True),
        )
    )
    version = result.scalar_one_or_none()
    if version is None:
        raise ConflictError("Agent runtime has no current executable version")
    return instance, employee, version
