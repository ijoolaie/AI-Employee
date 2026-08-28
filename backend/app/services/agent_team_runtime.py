"""Runtime bridge from Agent Team assignments to unified execution inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.services.agent_teams import AgentTeamError, TeamAssignment


@dataclass(frozen=True)
class TeamExecutionRequest:
    tenant_id: UUID
    executor_id: UUID
    correlation_id: str
    capability: str
    role: str
    approval_required: bool
    context: dict[str, Any]


class AgentTeamRuntimeBridge:
    """Translate orchestration state into a tenant-safe execution request."""

    def build_request(
        self,
        assignment: TeamAssignment,
        *,
        actor_tenant_id: UUID,
        context: dict[str, Any] | None = None,
    ) -> TeamExecutionRequest:
        if assignment.tenant_id != actor_tenant_id:
            raise AgentTeamError("runtime assignment tenant mismatch")
        payload = dict(context or {})
        payload.update(
            {
                "team_id": str(assignment.team_id),
                "capability": assignment.capability,
                "role": assignment.role,
                "correlation_id": assignment.correlation_id,
                "requires_approval": assignment.approval_required,
            }
        )
        return TeamExecutionRequest(
            tenant_id=assignment.tenant_id,
            executor_id=assignment.agent_id,
            correlation_id=assignment.correlation_id,
            capability=assignment.capability,
            role=assignment.role,
            approval_required=assignment.approval_required,
            context=payload,
        )
