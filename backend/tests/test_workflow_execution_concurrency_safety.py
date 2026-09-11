from pathlib import Path

SOURCE = Path(__file__).parents[1] / "app/services/workflow_service.py"
LEASE_SOURCE = Path(__file__).parents[1] / "app/services/workflow_execution_lease.py"
MODEL_SOURCE = Path(__file__).parents[1] / "app/models/workflow.py"


def test_workflow_recovery_is_fenced_by_expired_lease():
    source = SOURCE.read_text()
    lease_source = LEASE_SOURCE.read_text()
    assert "acquire_workflow_execution_lease" in source
    assert "allow_recovery=True" in lease_source
    assert "assert_workflow_execution_lease" in source
    assert "execution_lease_expires_at" in lease_source


def test_parallel_branch_does_not_reexecute_a_running_branch_after_nested_child_commit():
    source = SOURCE.read_text()
    lease_source = LEASE_SOURCE.read_text()
    model_source = MODEL_SOURCE.read_text()
    assert "acquire_parallel_branch_execution_lease" in source
    assert "assert_parallel_branch_execution_lease" in source
    assert "employee_run_id" in model_source
    assert "if branch.status == \"running\":" in lease_source
    assert "Parallel branch execution lease is still owned" in lease_source
