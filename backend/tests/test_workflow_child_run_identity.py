from pathlib import Path

ROOT = Path(__file__).parents[1]
RUN_MODEL = ROOT / "app/models/run.py"
MIGRATION = ROOT / "alembic/versions/f1a2b3c4d5e6_add_workflow_child_run_identity.py"
WORKFLOW = ROOT / "app/services/workflow_service.py"

def test_run_has_durable_workflow_child_identity():
    source = RUN_MODEL.read_text()
    assert "workflow_step_run_id" in source
    assert "workflow_parallel_branch_run_id" in source

def test_migration_persists_durable_child_identity():
    source = MIGRATION.read_text()
    assert "workflow_step_run_id" in source
    assert "workflow_parallel_branch_run_id" in source

def test_workflow_links_child_before_execution_commit():
    source = WORKFLOW.read_text()
    assert "child.workflow_step_run_id = step.id" in source
    assert "child.workflow_parallel_branch_run_id = branch.id" in source

def test_workflow_resolves_durable_child_before_replacement():
    source = WORKFLOW.read_text()
    assert "select(Run).where(Run.workflow_step_run_id == step.id)" in source
    assert "Durable child Run ended with status" in source
