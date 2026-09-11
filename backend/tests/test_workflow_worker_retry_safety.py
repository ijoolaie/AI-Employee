from pathlib import Path


def test_workflow_execution_exceptions_are_not_celery_retried() -> None:
    source = (
        Path(__file__).parents[1] / "app/workers/workflow_worker.py"
    ).read_text()

    assert "WORKFLOW_EXECUTION_LEASE_LOST" in source
    assert "await db.commit()" in source
    execution_section = source.split("asyncio.run(_run_async", 1)[1]
    assert "raise self.retry(exc=exc" not in execution_section
    assert "workflow_execution_failed" in source


def test_parallel_branch_execution_exceptions_are_not_retried() -> None:
    source = (
        Path(__file__).parents[1] / "app/workers/workflow_worker.py"
    ).read_text()

    branch_section = source.split("def execute_parallel_branch_task", 1)[1]
    assert "workflow_parallel_branch_failed" in branch_section
    assert "raise self.retry" not in branch_section
