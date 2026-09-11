from pathlib import Path


MIGRATION = Path(__file__).parents[1] / "alembic" / "versions" / "d5e6f7a8b9c0_fence_workflow_terminal_state.py"


def test_workflow_terminal_state_fence_is_database_enforced():
    source = MIGRATION.read_text()

    assert "CREATE TRIGGER trg_workflow_run_terminal_state_fence" in source
    assert "BEFORE UPDATE OF status ON workflow_runs" in source
    assert "OLD.status IN ('success', 'failed', 'cancelled', 'timed_out')" in source
    assert "NEW.status <> OLD.status" in source
    assert "ERRCODE = 'check_violation'" in source
    assert "DROP TRIGGER IF EXISTS trg_workflow_run_terminal_state_fence" in source
