from pathlib import Path


WORKFLOW_API_SOURCE = Path(__file__).parents[1] / "app/api/v1/workflows.py"


def test_workflow_run_api_uses_outbox_execution_path():
    source = WORKFLOW_API_SOURCE.read_text()

    assert 'kind="workflow.execute"' in source
    assert "enqueue(db" in source
    assert "workflow_run_id" in source


def test_workflow_run_api_does_not_directly_execute_worker():
    source = WORKFLOW_API_SOURCE.read_text()

    assert "workflow_executor.execute" not in source
    assert "run_worker.execute" not in source
