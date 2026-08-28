"""Tenant-safe Agent -> Agent handoff boundary."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.services.unified_execution import ExecutionError


class AgentHandoffService:
    """Create an explicit handoff payload without executing the target agent."""

    @staticmethod
    def handoff(*, current_agent_id: UUID, target_agent_id: UUID, current_tenant_id: UUID, target_tenant_id: UUID, context: dict[str, Any] | None = None, artifacts: list[dict[str, Any]] | None = None, requires_approval: bool = False) -> dict[str, Any]:
        if current_agent_id == target_agent_id:
            raise ExecutionError("agent cannot hand off to itself")
        if current_tenant_id != target_tenant_id:
            raise ExecutionError("cross-tenant agent handoff is forbidden")
        return {
            "source_agent_id": str(current_agent_id),
            "target_agent_id": str(target_agent_id),
            "tenant_id": str(current_tenant_id),
            "context": context or {},
            "artifacts": artifacts or [],
            "status": "waiting_approval" if requires_approval else "ready",
        }
