"""Tenant-scoped Agent Team orchestration contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


class AgentTeamError(RuntimeError):
    """Raised when team orchestration violates a contract."""


@dataclass(frozen=True)
class TeamMember:
    agent_id: UUID
    role: str
    capabilities: frozenset[str] = frozenset()


@dataclass
class AgentTeam:
    tenant_id: UUID
    name: str
    members: list[TeamMember] = field(default_factory=list)
    id: UUID = field(default_factory=uuid4)

    def add_member(self, member: TeamMember) -> None:
        if any(existing.agent_id == member.agent_id for existing in self.members):
            raise AgentTeamError("agent already belongs to team")
        self.members.append(member)


@dataclass(frozen=True)
class TeamAssignment:
    team_id: UUID
    tenant_id: UUID
    agent_id: UUID
    role: str
    capability: str
    correlation_id: str
    approval_required: bool = False


class AgentTeamService:
    """Orchestration boundary; actual execution remains on Unified Execution."""

    def assign(self, team: AgentTeam, *, tenant_id: UUID, capability: str, correlation_id: str | None = None, approval_required: bool = False) -> TeamAssignment:
        if team.tenant_id != tenant_id:
            raise AgentTeamError("team tenant mismatch")
        for member in team.members:
            if capability in member.capabilities:
                return TeamAssignment(team.id, tenant_id, member.agent_id, member.role, capability, correlation_id or str(uuid4()), approval_required)
        raise AgentTeamError(f"no team member can perform capability: {capability}")

    @staticmethod
    def handoff(assignment: TeamAssignment, *, target: TeamMember) -> TeamAssignment:
        if assignment.capability not in target.capabilities:
            raise AgentTeamError("handoff target lacks capability")
        return TeamAssignment(assignment.team_id, assignment.tenant_id, target.agent_id, target.role, assignment.capability, assignment.correlation_id, assignment.approval_required)
