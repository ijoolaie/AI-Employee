"""Central Agent tool authorization hook for the canonical Run worker."""
from __future__ import annotations

from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any, AsyncIterator
from uuid import UUID

from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError
from app.services.agent_governance import assert_agent_can_execute


_AGENT_CONTEXT: ContextVar[tuple[UUID, UUID] | None] = ContextVar(
    "agent_tool_governance_context", default=None
)
_INSTALLED = False


@asynccontextmanager
async def agent_tool_context(*, tenant_id: UUID, agent_instance_id: UUID) -> AsyncIterator[None]:
    """Bind Agent identity to all ToolRegistry calls in this task context."""
    token = _AGENT_CONTEXT.set((tenant_id, agent_instance_id))
    try:
        yield
    finally:
        _AGENT_CONTEXT.reset(token)


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
        tenant_id, agent_instance_id = context
        if db is None:
            raise ValidationAppError("Agent tool execution requires an active database context")
        if kwargs.get("tenant_id") != tenant_id:
            raise ValidationAppError("Agent tool execution tenant context mismatch")

        tool = registry.get(name)
        await assert_agent_can_execute(
            db,
            tenant_id=tenant_id,
            agent_instance_id=agent_instance_id,
            tool_name=name,
            required_permission=tool.required_permission,
            approval_granted=bool(kwargs.get("approval_granted", False)),
            requires_approval=tool.requires_approval,
        )
        return await original_execute(name, arguments, **kwargs)

    registry.execute = governed_execute  # type: ignore[method-assign]
    _INSTALLED = True


install()
