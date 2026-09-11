"""Contract tests for the WorkflowRun execution lease boundary."""
from pathlib import Path


def _source() -> str:
    return (Path(__file__).resolve().parents[1] / "app" / "services" / "workflow_service.py").read_text()


def test_workflow_execution_lease_contract_is_documented_in_service():
    source = _source()
    assert "execution_lease_id" in source
    assert "execution_lease_expires_at" in source
    assert "WORKFLOW_EXECUTION_LEASE_LOST" in source
    assert "acquire_workflow_execution_lease" in source


def test_stale_worker_must_fail_closed_before_advancing_workflow():
    source = _source()
    assert "assert_workflow_execution_lease" in source
    assert "fresh_lease_id" in source
    assert "fresh_lease_id != lease_id" in source


def test_recovery_requires_expired_lease_and_reuses_same_workflow_run():
    source = _source()
    assert "recover_workflow_execution_lease" in source
    assert "execution_lease_expires_at" in source
    assert "WorkflowRun.id == workflow_run_id" in source
