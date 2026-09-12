from pathlib import Path

from app.models.run import Run

ROOT = Path(__file__).parents[1]
RUN_MODEL = ROOT / "app/models/run.py"
MIGRATION = ROOT / "alembic/versions/f1a2b3c4d5e6_add_workflow_child_run_identity.py"
WORKFLOW = ROOT / "app/services/workflow_service.py"


def test_run_has_durable_workflow_child_identity():
    source = RUN_MODEL.read_text()
    assert "workflow_step_run_id" in source
    assert "workflow_parallel_branch_run_id" in source
    assert "workflow_parallel_branch_step_key" in source


def test_parallel_identity_is_scoped_to_branch_and_step():
    constraint = next(
        c for c in Run.__table__.constraints
        if getattr(c, "name", None) == "uq_runs_workflow_parallel_branch_step_identity"
    )
    assert [column.name for column in constraint.columns] == [
        "workflow_parallel_branch_run_id",
        "workflow_parallel_branch_step_key",
    ]


def test_workflow_child_fks_use_alter_ddl_to_break_metadata_cycle():
    step_fk = Run.__table__.c.workflow_step_run_id.foreign_keys.pop()
    branch_fk = Run.__table__.c.workflow_parallel_branch_run_id.foreign_keys.pop()
    try:
        assert step_fk.use_alter is True
        assert branch_fk.use_alter is True
    finally:
        Run.__table__.c.workflow_step_run_id.foreign_keys.add(step_fk)
        Run.__table__.c.workflow_parallel_branch_run_id.foreign_keys.add(branch_fk)


def test_migration_persists_durable_child_identity_on_current_head():
    source = MIGRATION.read_text()
    assert "revision = \"f1a2b3c4d5e6\"" in source
    assert "down_revision = \"f9a0b1c2d3e4\"" in source
    assert "workflow_step_run_id" in source
    assert "workflow_parallel_branch_run_id" in source
    assert "workflow_parallel_branch_step_key" in source
    assert "uq_runs_workflow_parallel_branch_step_identity" in source


def test_workflow_persists_identity_before_execution_commit():
    source = WORKFLOW.read_text()
    serial_identity = 'child.workflow_step_run_id = step.id'
    parallel_identity = 'child.workflow_parallel_branch_run_id = branch.id'
    parallel_key = 'child.workflow_parallel_branch_step_key = str(definition["key"])'
    assert serial_identity in source
    assert parallel_identity in source
    assert parallel_key in source

    parallel_start = source.index(parallel_identity)
    parallel_key_pos = source.index(parallel_key, parallel_start)
    parallel_commit = source.index("await db.commit()", parallel_key_pos)
    parallel_execute = source.index("await run_service.execute_run(db, run_id=child.id)", parallel_commit)
    assert parallel_key_pos < parallel_commit < parallel_execute

    serial_start = source.index(serial_identity)
    serial_commit = source.index("await db.commit()", serial_start)
    serial_execute = source.index("await run_service.execute_run(db, run_id=child.id)", serial_commit)
    assert serial_start < serial_commit < serial_execute


def test_parallel_recovery_identity_is_branch_and_step_specific():
    source = WORKFLOW.read_text()
    lookup = "select(Run).where(\n                            Run.workflow_parallel_branch_run_id == branch.id,\n                            Run.workflow_parallel_branch_step_key == str(definition[\"key\"]),\n                        )"
    assert lookup in source
    assert "branch.current_step_position = position + 1" in source
    assert "branch.employee_run_id = None" in source


def test_workflow_resolves_durable_child_before_replacement():
    source = WORKFLOW.read_text()
    assert "select(Run).where(Run.workflow_step_run_id == step.id)" in source
    assert "Run.workflow_parallel_branch_run_id == branch.id" in source
    assert "Run.workflow_parallel_branch_step_key == str(definition[\"key\"])" in source
    assert "WORKFLOW_CHILD_RETRY_UNSAFE: durable parallel branch Run ended with status" in source
