from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (BACKEND / path).read_text(encoding="utf-8")


def test_run_worker_does_not_create_runs_directly():
    """Execution workers must execute durable Runs, not create new ones."""
    source = _read("app/workers/run_worker.py")
    assert "create_run(" not in source


def test_side_effect_tools_require_execution_permission():
    """Any side-effect tool must remain behind the run.execute permission boundary."""
    source = _read("app/ai/tool_registry.py")

    blocks = source.split("RegisteredTool(")
    for block in blocks[1:]:
        if "side_effects=True" in block:
            assert "required_permission" in block
            assert "run.execute" in block


def test_workflow_models_keep_employee_run_binding():
    """Workflow child execution must preserve durable employee run linkage."""
    model = _read("app/models/workflow.py")
    service = _read("app/services/workflow_service.py")

    assert "employee_run_id" in model
    assert "employee_run_id" in service


def test_known_run_creation_entrypoints_exist():
    """Guard the current Run creation topology against accidental parallel paths."""
    expected = [
        "app/api/v1/runs.py",
        "app/api/v1/channel_webhooks.py",
        "app/services/customer_channel_service.py",
        "app/services/agent_execution_adapter.py",
        "app/services/workflow_service.py",
    ]

    for path in expected:
        assert (BACKEND / path).exists(), path


def test_run_creation_persists_lifecycle_audit_event():
    """Every durable Run creation must emit exactly one tenant-scoped audit event."""
    source = _read("app/services/run_service.py")

    assert source.count('action="run.created"') == 1
    assert 'resource_type="run"' in source
    assert 'resource_id=run.id' in source
    assert 'actor_id=created_by' in source
    assert '"employee_id": str(employee.id)' in source
    assert '"employee_version": version.version_number' in source
    assert '"agent_instance_id": str(agent_instance_id)' in source
