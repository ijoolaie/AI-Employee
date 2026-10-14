"""Runtime enforcement for governed AI workforce role operations.

This layer binds the declarative workforce-role catalog to the existing Agent
execution adapter. Approval-gated operations require a persisted approval bound
to the exact tenant, Run, tool, tool-call ID, and arguments.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstance
from app.models.tool_approval import ToolApprovalRequest
from app.services.ai_workforce_roles import (
    assert_workforce_capability_contract_snapshot,
    assert_workforce_tool_binding,
    get_workforce_role,
    is_operation_allowed,
    WORKFORCE_ROLES,
)
from app.services.agent_governance import current_agent_execution_context
from app.services.workforce_delegation_service import assert_operation_delegated


def workforce_operation_for_tool(tool_name: str) -> tuple[str, str] | None:
    """Resolve a registered workforce tool to its catalog role/operation binding."""
    for role in WORKFORCE_ROLES:
        for contract in role.capability_contract:
            if tool_name in contract.tool_names:
                return role.code, contract.operation
    return None


async def assert_workforce_tool_execution(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    agent_instance_id: UUID,
    tool_name: str,
    approval_request_id: UUID | None = None,
    run_id: UUID | None = None,
    tool_call_id: str | None = None,
    arguments: dict | None = None,
) -> None:
    """Enforce role/capability/tool binding at the canonical Run tool boundary."""
    binding = workforce_operation_for_tool(tool_name)
    if binding is None:
        return

    from sqlalchemy import select

    result = await db.execute(
        select(AgentInstance).where(
            AgentInstance.id == agent_instance_id,
            AgentInstance.tenant_id == tenant_id,
        )
    )
    agent = result.scalar_one_or_none()
    if agent is None:
        raise ValidationAppError("Workforce tool execution requires a tenant-scoped AgentInstance")

    role_code, operation = binding
    actual_role = str((agent.configuration or {}).get("workforce_role_code") or "").strip()
    if actual_role != role_code:
        raise ValidationAppError(
            "Workforce tool is not bound to the executing Agent role",
            details={"role": actual_role or None, "required_role": role_code, "operation": operation, "tool": tool_name},
        )

    assert_workforce_tool_binding(role_code, operation, tool_name)
    await assert_workforce_operation(
        db,
        agent=agent,
        operation=operation,
        approval_request_id=approval_request_id,
        run_id=run_id,
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        arguments=arguments,
    )


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

    assert_workforce_capability_contract_snapshot(
        role.code,
        (agent.configuration or {}).get("workforce_capability_contract"),
    )

    approved_gated_operation = False
    if operation in role.approval_required_operations:
        if not all((approval_request_id, run_id, tool_name, tool_call_id)) or arguments is None:
            raise ValidationAppError(
                "Human approval is required for this workforce operation",
                details={"role": role.code, "operation": operation},
            )
        assert_workforce_tool_binding(role.code, operation, tool_name)
        approval_result = await db.execute(
            select(ToolApprovalRequest).where(
                ToolApprovalRequest.id == approval_request_id,
                ToolApprovalRequest.tenant_id == agent.tenant_id,
                ToolApprovalRequest.run_id == run_id,
                ToolApprovalRequest.tool_name == tool_name,
                ToolApprovalRequest.tool_call_id == tool_call_id,
                ToolApprovalRequest.status == "approved",
            )
        )
        approval = approval_result.scalar_one_or_none()
        if approval is None or approval.arguments != arguments:
            raise ValidationAppError(
                "Human approval is missing or does not match this workforce tool call",
                details={"role": role.code, "operation": operation},
            )
        approved_gated_operation = True
    if operation not in role.allowed_routine_operations and operation not in role.approval_required_operations:
        raise ValidationAppError(
            "Workforce role is not authorized for this operation",
            details={"role": role.code, "operation": operation},
        )

    if role.code != "ai_internal_manager":
        if not approved_gated_operation and not is_operation_allowed(role.code, operation):
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
