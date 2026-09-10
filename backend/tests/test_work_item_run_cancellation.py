from pathlib import Path


MIGRATION = Path(__file__).parents[1] / "alembic" / "versions" / "c4d5e6f7a8b9_cancel_agent_run_with_work_item.py"


def test_work_item_cancellation_cancels_only_pre_execution_agent_runs():
    source = MIGRATION.read_text(encoding="utf-8")
    assert 'NEW.status = \'cancelled\'' in source
    assert "NEW.executor_type = 'agent'" in source
    assert "NEW.output_data ->> 'run_id'" in source
    assert "status IN ('pending', 'waiting')" in source
    assert "SET status = 'cancelled'" in source


def test_work_item_cancellation_is_tenant_scoped_and_auditable():
    source = MIGRATION.read_text(encoding="utf-8")
    assert "AND tenant_id = NEW.tenant_id" in source
    assert "'RUN_CANCELLED'" in source
    assert "DROP TRIGGER IF EXISTS" in source
    assert "DROP FUNCTION IF EXISTS" in source
