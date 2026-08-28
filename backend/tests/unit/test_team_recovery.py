from uuid import uuid4

import pytest

from app.services.team_recovery import RecoveryError, TeamRun, TeamRunStatus


def test_completion_gate_requires_all_members():
    tenant = uuid4()
    run = TeamRun(tenant_id=tenant, correlation_id="corr-1", required_members={"a", "b"})
    run.mark_member_complete("a")
    with pytest.raises(RecoveryError, match="completion gates"):
        run.complete()
    run.mark_member_complete("b")
    run.complete()
    assert run.status is TeamRunStatus.COMPLETED


def test_restore_is_tenant_and_correlation_safe():
    tenant = uuid4()
    run = TeamRun(tenant_id=tenant, correlation_id="corr-1")
    snapshot = run.checkpoint()
    with pytest.raises(RecoveryError, match="tenant mismatch"):
        run.restore(tenant_id=uuid4(), snapshot=snapshot)
    with pytest.raises(RecoveryError, match="correlation mismatch"):
        run.restore(tenant_id=tenant, snapshot={**snapshot, "correlation_id": "other"})


def test_terminal_state_cannot_be_mutated():
    run = TeamRun(tenant_id=uuid4(), correlation_id="corr-2")
    run.fail("worker failed")
    with pytest.raises(RecoveryError, match="terminal"):
        run.mark_member_complete("a")
