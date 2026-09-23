"""Runtime enforcement for governed AI workforce role operations.

This layer binds the declarative workforce-role catalog to the existing Agent
execution adapter. It never provisions roles and never grants approval-gated
operations.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstance
from app.services.ai_workforce_roles import get_workforce_role, is_operation_allowed
from app.services.agent_governance import current_agent_execution_context
from app.services.workforce_delegation_service import assert_operation_delegated


async def assert_workforce_operation(
    db: AsyncSession,
    *,
    agent: AgentInstance,
    operation: str,
    affected_employee_id: UUID | None = None,
) -> None:
    """Fail closed unless the Agent's catalog role permits the requested operation."""
    role_code = (agent.configuration or {}).get("workforce_role_code")
    if not role_code:
        raise ValidationAppError(
            "Workforce role identity is required for governed workforce operations"
        )

    try:
        role = get_workforce_role(str(role_code))
    except KeyError as exc:
        raise ValidationAppError("Unknown workforce role; operation denied") from exc

    if operation in role.approval_required_operations:
        raise ValidationAppError(
            "Human approval is required for this workforce operation",
            details={"role": role.code, "operation": operation},
        )
    if operation not in role.allowed_routine_operations:
        raise ValidationAppError(
            "Workforce role is not authorized for this operation",
            details={"role": role.code, "operation": operation},
        )

    if role.code != "ai_internal_manager":
        if not is_operation_allowed(role.code, operation):
            raise ValidationAppError("Workforce operation denied by role policy")
        return

    context = current_agent_execution_context()
    if context is None:
        raise ValidationAppError("Internal Manager operation requires governed runtime context")
    runtime_tenant_id, runtime_agent_id, run_id, _employee_id, _version_id = context
    if runtime_tenant_id != agent.tenant_id or runtime_agent_id != agent.id:
        raise ValidationAppError("Internal Manager runtime identity mismatch")
    if run_id is None:
        raise ValidationAppError("Internal Manager operation requires a durable Run identity")

    await assert_operation_delegated(
        db,
        tenant_id=agent.tenant_id,
        manager_agent_instance_id=agent.id,
        operation=operation,
        employee_id=affected_employee_id,
    )
