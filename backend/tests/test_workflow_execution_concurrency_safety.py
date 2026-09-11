from pathlib import Path

SOURCE = Path(__file__).parents[1] / "app/services/workflow_service.py"


def test_workflow_does_not_reenter_a_running_parent_after_nested_child_commit():
    source = SOURCE.read_text()
    assert 'if run.status not in {"pending", "waiting_approval"}:' in source
    assert 'if run.status not in {"pending", "running", "waiting_approval"}:' not in source


def test_parallel_branch_does_not_reexecute_a_running_branch_after_nested_child_commit():
    source = SOURCE.read_text()
    assert 'if branch is None or branch.status in {"success", "running"}:' in source
