from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.team_operational_health import team_health


def make_run(status="running", required=None, completed=None):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        correlation_id="corr-health",
        status=SimpleNamespace(value=status),
        required_members=required or set(),
        completed_members=completed or set(),
    )


def test_health_surfaces_blocked_members():
    run = make_run(required={"a", "b"}, completed={"a"})
    result = team_health(run, actor_tenant_id=run.tenant_id)
    assert result["blocked_members"] == ["b"]
    assert result["ready"] is False


def test_health_surfaces_approval_and_failure():
    waiting = make_run(status="waiting_approval")
    failed = make_run(status="failed")
    assert team_health(waiting, actor_tenant_id=waiting.tenant_id)["waiting_approval"] is True
    assert team_health(failed, actor_tenant_id=failed.tenant_id)["failed"] is True


def test_health_rejects_cross_tenant_access():
    run = make_run()
    with pytest.raises(PermissionError, match="tenant mismatch"):
        team_health(run, actor_tenant_id=uuid4())
