"""Central Agent tool authorization hook for the canonical Run worker."""
from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any, AsyncIterator
from uuid import UUID

from sqlalchemy import select

from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError
from app.models.tool_approval import ToolApprovalRequest
from app.services.agent_governance import assert_agent_can_execute


_AGENT_CONTEXT: ContextVar[tuple[UUID, UUID, UUID] | None] = ContextVar(
    "agent_tool_governance_context", default=None
)
_INSTALLED = False


@asynccontextmanager
async def agent_tool_context(
    *,
    tenant_id: UUID,
    agent_instance_id: UUID,
    run_id: UUID,
) -> AsyncIterator[None]:
    """Bind tenant, Agent identity, and canonical Run to ToolRegistry calls."""
    token = _AGENT_CONTEXT.set((tenant_id, agent_instance_id, run_id))
    try:
        yield
    finally:
        _AGENT_CONTEXT.reset(token)


async def _has_authoritative_approval(
    db: Any,
    *,
    tenant_id: UUID,
    run_id: UUID,
    tool_name: str,
    arguments: dict[str, Any],
) -> bool:
    """Require exactly one approved request matching the exact tool payload.

    A boolean supplied by a caller is never treated as authorization. The
    approval must belong to the same tenant/run, name the same tool, contain
    the same arguments, and be in the approved state. Ambiguous duplicate
    approvals fail closed.
    """
    result = await db.execute(
        select(ToolApprovalRequest).where(
            ToolApprovalRequest.tenant_id == tenant_id,
            ToolApprovalRequest.run_id == run_id,
            ToolApprovalRequest.tool_name == tool_name,
            ToolApprovalRequest.status == "approved",
        )
    )
    matches = [item for item in result.scalars().all() if item.arguments == arguments]
    return len(matches) == 1


def install() -> None:
    """Install one centralized, fail-closed Agent authorization wrapper."""
    global _INSTALLED
    if _INSTALLED:
        return

    original_execute = registry.execute

    @wraps(original_execute)
    async def governed_execute(name: str, arguments: dict[str, Any], **kwargs: Any) -> Any:
        context = _AGENT_CONTEXT.get()
        if context is None:
            return await original_execute(name, arguments, **kwargs)

        db = kwargs.get("db")
        tenant_id, agent_instance_id, run_id = context
        if db is None:
            raise ValidationAppError("Agent tool execution requires an active database context")
        if kwargs.get("tenant_id") != tenant_id:
            raise ValidationAppError("Agent tool execution tenant context mismatch")

        tool = registry.get(name)
        approval_granted = False
        if tool.requires_approval:
            # The caller's boolean is deliberately ignored. Only the durable
            # ApprovalRequest can authorize the side effect.
            approval_granted = await _has_authoritative_approval(
                db,
                tenant_id=tenant_id,
                run_id=run_id,
                tool_name=name,
                arguments=arguments,
            )
            if not approval_granted:
                raise ValidationAppError(
                    "Human approval required for Agent tool execution",
                    details={"tool": name, "run_id": str(run_id)},
                )

        await assert_agent_can_execute(
            db,
            tenant_id=tenant_id,
            agent_instance_id=agent_instance_id,
            tool_name=name,
            required_permission=tool.required_permission,
            approval_granted=approval_granted,
            requires_approval=tool.requires_approval,
        )
        kwargs["approval_granted"] = approval_granted
        return await original_execute(name, arguments, **kwargs)

    registry.execute = governed_execute  # type: ignore[method-assign]
    _INSTALLED = True


install()
