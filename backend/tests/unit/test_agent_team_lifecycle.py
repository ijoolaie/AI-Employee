from uuid import uuid4

import pytest

from app.services.agent_teams import (
    AgentTeam,
    AgentTeamError,
    AgentTeamService,
    TeamMember,
    TeamRun,
    TeamRunStatus,
)


def test_approval_propagates_through_handoff():
    tenant = uuid4()
    team = AgentTeam(tenant_id=tenant, name="ops")
    source = TeamMember(uuid4(), "worker", frozenset({"deploy"}))
    target = TeamMember(uuid4(), "reviewer", frozenset({"deploy"}))
    team.add_member(source)
    team.add_member(target)

    assignment = AgentTeamService().assign(
        team, tenant_id=tenant, capability="deploy", correlation_id="corr-9", approval_required=True
    )
    run = TeamRun(team.id, tenant, "corr-9")
    run.transition(TeamRunStatus.RUNNING, actor_tenant_id=tenant)
    run.propagate_assignment(assignment, actor_tenant_id=tenant)

    assert run.status == TeamRunStatus.WAITING_APPROVAL
    assert run.approval_required is True
    assert run.evidence[-1]["correlation_id"] == "corr-9"


def test_terminal_team_run_cannot_transition_again():
    tenant = uuid4()
    run = TeamRun(uuid4(), tenant, "corr-1")
    run.transition(TeamRunStatus.FAILED, actor_tenant_id=tenant, reason="worker failed")

    with pytest.raises(AgentTeamError, match="terminal"):
        run.transition(TeamRunStatus.COMPLETED, actor_tenant_id=tenant)


def test_team_run_rejects_cross_tenant_transition():
    run = TeamRun(uuid4(), uuid4(), "corr-2")
    with pytest.raises(AgentTeamError, match="tenant mismatch"):
        run.transition(TeamRunStatus.RUNNING, actor_tenant_id=uuid4())
