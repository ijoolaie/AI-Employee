"""Capability, approval, secret, concurrency and tool-scope checks."""

from __future__ import annotations

from typing import Any
from uuid import UUID


class ExecutionPolicyError(RuntimeError):
    """Raised when an execution policy denies an operation."""



class ExecutionPolicy:
    """Pure policy boundary for unified execution."""

    @staticmethod
    def authorize(
        *,
        tenant_id: UUID,
        actor_tenant_id: UUID,
        capabilities: set[str],
        required_capability: str | None = None,
        tool: str | None = None,
        allowed_tools: set[str] | None = None,
        budget_used: float = 0.0,
        budget_limit: float | None = None,
        requires_approval: bool = False,
        approved: bool = False,
        active_executions: int = 0,
        concurrency_limit: int | None = None,
        secret_names: set[str] | None = None,
        requested_secret: str | None = None,
        export_secret: bool = False,
    ) -> dict[str, Any]:
        if tenant_id != actor_tenant_id:
            raise ExecutionPolicyError("execution policy tenant mismatch")
        if required_capability and required_capability not in capabilities:
            raise ExecutionPolicyError("required capability is not authorized")
        if tool and tool not in (allowed_tools or set()):
            raise ExecutionPolicyError("tool is outside executor scope")
        if budget_limit is not None and budget_used >= budget_limit:
            raise ExecutionPolicyError("executor budget exceeded")
        if requires_approval and not approved:
            return {"authorized": False, "waiting_for_approval": True}
        if concurrency_limit is not None and active_executions >= concurrency_limit:
            raise ExecutionPolicyError("executor concurrency limit exceeded")
        if requested_secret and requested_secret not in (secret_names or set()):
            raise ExecutionPolicyError("secret is outside executor scope")
        if export_secret:
            raise ExecutionPolicyError("secrets are non-exportable")
        return {
            "authorized": True,
            "waiting_for_approval": False,
            "tenant_id": str(tenant_id),
            "tool": tool,
        }
