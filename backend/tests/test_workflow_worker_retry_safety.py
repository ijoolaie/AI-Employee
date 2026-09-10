from pathlib import Path


def test_workflow_execution_exceptions_are_not_celery_retried() -> None:
    source = (
        Path(__file__).parents[1] / "app/workers/workflow_worker.py"
    ).read_text()

    assert "execute_workflow() persists a terminal failed state" in source
    assert "await db.commit()" in source
    assert "raise self.retry(exc=exc" not in source
    assert "workflow_execution_failed" in source


def test_parallel_branch_execution_exceptions_are_not_retried() -> None:
    source = (
        Path(__file__).parents[1] / "app/workers/workflow_worker.py"
    ).read_text()

    assert "workflow_parallel_branch_failed" in source
    assert "raise self.retry(exc=exc" not in source
