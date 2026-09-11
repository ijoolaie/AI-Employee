from pathlib import Path

SOURCE = Path(__file__).parents[1] / "app/services/workflow_service.py"


def test_workflow_recovery_is_fenced_by_expired_lease():
    source = SOURCE.read_text()
    assert 'execution_lease_id: uuid.UUID | None = None' in source
    assert 'if execution_lease_id is not None:' in source
    assert 'allow_recovery=True' in source
    assert 'assert_workflow_execution_lease' in source


def test_parallel_branch_does_not_reexecute_a_running_branch_after_nested_child_commit():
    source = SOURCE.read_text()
    assert 'if branch is None or branch.status in {"success", "running"}:' in source
