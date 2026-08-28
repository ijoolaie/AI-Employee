from uuid import uuid4

import pytest

from app.services.agent_teams import AgentTeam, AgentTeamError, AgentTeamService, TeamMember


def test_team_routes_capability_with_correlation():
    tenant = uuid4()
    member = TeamMember(uuid4(), "researcher", frozenset({"research"}))
    team = AgentTeam(tenant, "ops", [member])

    assignment = AgentTeamService().assign(team, tenant_id=tenant, capability="research", correlation_id="corr-9")

    assert assignment.agent_id == member.agent_id
    assert assignment.correlation_id == "corr-9"


def test_team_rejects_cross_tenant_assignment():
    team = AgentTeam(uuid4(), "ops")
    team.add_member(TeamMember(uuid4(), "worker", frozenset({"execute"})))

    with pytest.raises(AgentTeamError, match="tenant mismatch"):
        AgentTeamService().assign(team, tenant_id=uuid4(), capability="execute")


def test_handoff_preserves_correlation_and_checks_capability():
    tenant = uuid4()
    first = TeamMember(uuid4(), "worker", frozenset({"execute"}))
    target = TeamMember(uuid4(), "reviewer", frozenset({"execute"}))
    team = AgentTeam(tenant, "ops", [first, target])
    assignment = AgentTeamService().assign(team, tenant_id=tenant, capability="execute", correlation_id="corr-10")

    handed_off = AgentTeamService.handoff(assignment, target=target)

    assert handed_off.agent_id == target.agent_id
    assert handed_off.correlation_id == "corr-10"
