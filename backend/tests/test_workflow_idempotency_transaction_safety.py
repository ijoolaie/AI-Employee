from pathlib import Path


SOURCE = Path(__file__).parents[1] / "app/services/workflow_service.py"


def test_workflow_run_idempotency_conflict_uses_savepoint_not_full_transaction_rollback():
    source = SOURCE.read_text()
    start = source.index("async def create_workflow_run")
    end = source.index("\n\nasync def replay_workflow_run", start)
    function = source[start:end]

    assert "async with db.begin_nested():" in function
    assert "await db.rollback()" not in function
