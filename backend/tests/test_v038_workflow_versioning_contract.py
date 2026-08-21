import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_workflow_version_model_has_immutable_contract_fields():
    source = (ROOT / "app/models/workflow.py").read_text()
    assert "execution_contract" in source
    assert "content_hash" in source


def test_workflow_api_exposes_version_and_replay_contract():
    source = (ROOT / "app/api/v1/workflows.py").read_text()
    for route in [
        "/{workflow_id}/versions",
        "/{workflow_id}/versions/{version_id}",
        "/{workflow_id}/versions/{version_id}/activate",
        "/{workflow_id}/runs/{run_id}/replay",
    ]:
        assert route in source


def test_workflow_service_pins_employee_version_and_replay_source():
    source = (ROOT / "app/services/workflow_service.py").read_text()
    assert "employee_version_id" in source
    assert "execution_contract" in source
    assert "replay_source_version_id" in source
    assert "workflow_version_id=source.workflow_version_id" in source


def test_migration_declares_database_immutability_guard():
    path = ROOT / "alembic/versions/f8d9e0a1b234_workflow_versioning_execution_contract.py"
    source = path.read_text()
    assert "trg_workflow_versions_immutable" in source
    assert "prevent_workflow_version_mutation" in source
    assert "uq_workflow_single_current_version" in source
    assert "uq_workflow_version_number" in source


def test_python_files_compile_to_ast():
    files = [
        ROOT / "app/models/workflow.py",
        ROOT / "app/services/workflow_service.py",
        ROOT / "app/services/run_service.py",
        ROOT / "app/api/v1/workflows.py",
        ROOT / "app/schemas/workflow.py",
        ROOT / "alembic/versions/f8d9e0a1b234_workflow_versioning_execution_contract.py",
    ]
    for path in files:
        ast.parse(path.read_text(), filename=str(path))
