from uuid import uuid4

import pytest

from app.services.agent_team_runtime import AgentTeamRuntimeBridge
from app.services.agent_teams import AgentTeamError, TeamAssignment


def test_runtime_bridge_preserves_correlation_and_approval():
    tenant = uuid4()
    assignment = TeamAssignment(
        team_id=uuid4(),
        tenant_id=tenant,
        agent_id=uuid4(),
        role="reviewer",
        capability="review:execute",
        correlation_id="corr-123",
        approval_required=True,
    )

    request = AgentTeamRuntimeBridge().build_request(
        assignment,
        actor_tenant_id=tenant,
        context={"source": "team"},
    )

    assert request.correlation_id == "corr-123"
    assert request.approval_required is True
    assert request.context["requires_approval"] is True
    assert request.context["source"] == "team"


def test_runtime_bridge_rejects_cross_tenant_dispatch():
    assignment = TeamAssignment(
        team_id=uuid4(),
        tenant_id=uuid4(),
        agent_id=uuid4(),
        role="worker",
        capability="work:execute",
        correlation_id="corr-1",
    )

    with pytest.raises(AgentTeamError, match="tenant mismatch"):
        AgentTeamRuntimeBridge().build_request(assignment, actor_tenant_id=uuid4())
