from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.team_completion_summary import summarize_team_run


def test_completion_summary_aggregates_members_and_sanitizes_evidence():
    tenant = uuid4()
    run = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        correlation_id="corr-9",
        status=SimpleNamespace(value="completed"),
        required_members={"planner", "worker"},
        completed_members={"planner"},
        evidence=[{"event": "completed", "api_token": "hidden"}],
    )

    result = summarize_team_run(run, actor_tenant_id=tenant)

    assert result["pending_members"] == ["worker"]
    assert result["is_complete"] is False
    assert result["evidence"] == [{"event": "completed"}]


def test_completion_summary_rejects_cross_tenant_access():
    run = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        correlation_id="corr-10",
        status=SimpleNamespace(value="running"),
        required_members=set(),
        completed_members=set(),
        evidence=[],
    )

    with pytest.raises(PermissionError, match="tenant mismatch"):
        summarize_team_run(run, actor_tenant_id=uuid4())
