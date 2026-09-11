"""Contract tests for the WorkflowRun execution lease boundary."""
from pathlib import Path


def _source() -> str:
    return (Path(__file__).resolve().parents[1] / "app" / "services" / "workflow_service.py").read_text()


def _lease_source() -> str:
    return (Path(__file__).resolve().parents[1] / "app" / "services" / "workflow_execution_lease.py").read_text()


def test_workflow_execution_lease_contract_is_documented_in_service():
    source = _source()
    assert "execution_lease_id" in source
    assert "execution_lease_expires_at" in source
    assert "WORKFLOW_EXECUTION_LEASE_LOST" in source
    assert "acquire_workflow_execution_lease" in source


def test_stale_worker_must_fail_closed_before_advancing_workflow():
    source = _source()
    lease_source = _lease_source()
    assert "assert_workflow_execution_lease" in source
    assert "fresh_lease_id" in lease_source
    assert "fresh_lease_id != lease_id" in lease_source
    assert "execution_lease_expires_at <= now" in lease_source


def test_recovery_requires_expired_lease_and_reuses_same_workflow_run():
    source = _source()
    lease_source = _lease_source()
    assert "recover_workflow_execution_lease" in lease_source
    assert "execution_lease_expires_at" in lease_source
    assert "WorkflowRun.id == workflow_run_id" in lease_source
    assert "allow_recovery=True" in source


def test_waiting_states_release_execution_lease_and_approval_can_reacquire():
    source = _source()
    lease_source = _lease_source()
    assert source.count("run.execution_lease_id = None") >= 2
    assert "run.status in {\"pending\", \"waiting_approval\"}" in lease_source
    assert "run.status = \"running\"" in lease_source
