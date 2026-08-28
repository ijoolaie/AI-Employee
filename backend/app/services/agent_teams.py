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


class AgentTeamService:
    """Small orchestration boundary; execution remains on Unified Execution."""

    def assign(self, team: AgentTeam, *, tenant_id: UUID, capability: str, correlation_id: str | None = None) -> TeamAssignment:
        if team.tenant_id != tenant_id:
            raise AgentTeamError("team tenant mismatch")
        for member in team.members:
            if capability in member.capabilities:
                return TeamAssignment(
                    team_id=team.id,
                    tenant_id=tenant_id,
                    agent_id=member.agent_id,
                    role=member.role,
                    capability=capability,
                    correlation_id=correlation_id or str(uuid4()),
                )
        raise AgentTeamError(f"no team member can perform capability: {capability}")

    @staticmethod
    def handoff(assignment: TeamAssignment, *, target: TeamMember) -> TeamAssignment:
        if assignment.tenant_id is None:
            raise AgentTeamError("invalid assignment tenant")
        if assignment.capability not in target.capabilities:
            raise AgentTeamError("handoff target lacks capability")
        return TeamAssignment(
            team_id=assignment.team_id,
            tenant_id=assignment.tenant_id,
            agent_id=target.agent_id,
            role=target.role,
            capability=assignment.capability,
            correlation_id=assignment.correlation_id,
        )
