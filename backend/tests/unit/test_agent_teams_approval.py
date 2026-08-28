from uuid import uuid4

from app.services.agent_teams import AgentTeam, AgentTeamService, TeamMember


def test_handoff_preserves_approval_and_correlation():
    tenant = uuid4()
    source = TeamMember(uuid4(), "worker", frozenset({"review"}))
    target = TeamMember(uuid4(), "reviewer", frozenset({"review"}))
    team = AgentTeam(tenant, "ops", [source, target])
    assignment = AgentTeamService().assign(
        team,
        tenant_id=tenant,
        capability="review",
        correlation_id="corr-9",
        approval_required=True,
    )

    handoff = AgentTeamService.handoff(assignment, target=target)

    assert handoff.agent_id == target.agent_id
    assert handoff.correlation_id == "corr-9"
    assert handoff.approval_required is True
