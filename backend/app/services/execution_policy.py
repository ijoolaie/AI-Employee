"""Capability and tool-scope checks for unified execution."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.services.unified_execution import ExecutionError


class ExecutionPolicy:
    """Pure policy boundary for capability, tool, and budget checks."""

    @staticmethod
    def authorize(*, tenant_id: UUID, actor_tenant_id: UUID, capabilities: set[str], required_capability: str | None = None, tool: str | None = None, allowed_tools: set[str] | None = None, budget_used: float = 0.0, budget_limit: float | None = None) -> dict[str, Any]:
        if tenant_id != actor_tenant_id:
            raise ExecutionError("execution policy tenant mismatch")
        if required_capability and required_capability not in capabilities:
            raise ExecutionError("required capability is not authorized")
        if tool and tool not in (allowed_tools or set()):
            raise ExecutionError("tool is outside executor scope")
        if budget_limit is not None and budget_used >= budget_limit:
            raise ExecutionError("executor budget exceeded")
        return {"authorized": True, "tenant_id": str(tenant_id), "tool": tool}
