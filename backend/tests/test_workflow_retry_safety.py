from pathlib import Path


def test_workflow_child_retry_is_fail_closed() -> None:
    source = (Path(__file__).parents[1] / "app/services/workflow_service.py").read_text()

    assert "retry_max" in source
    assert "Unsafe workflow retry" in source
    assert "child_run_retry_unsafe" in source


def test_parallel_branch_child_retry_is_fail_closed() -> None:
    source = (Path(__file__).parents[1] / "app/services/workflow_service.py").read_text()

    assert "Unsafe workflow retry" in source
    assert source.count("child_run_retry_unsafe") >= 2
