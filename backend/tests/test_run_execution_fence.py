from pathlib import Path


def test_run_worker_uses_locked_execution_fence():
    worker = Path(__file__).parents[1] / "app" / "workers" / "run_worker.py"
    source = worker.read_text(encoding="utf-8")

    assert "from app.services.run_execution_fence import execute_run_locked" in source
    assert "execute_run_locked(db, run_id=parsed_run_id)" in source
    assert "run_service.execute_run(db, run_id=parsed_run_id)" not in source


def test_run_execution_fence_locks_run_before_service_execution():
    fence = Path(__file__).parents[1] / "app" / "services" / "run_execution_fence.py"
    source = fence.read_text(encoding="utf-8")

    assert "select(Run).where(Run.id == run_id).with_for_update()" in source
    assert "return await run_service.execute_run(db, run_id=run_id)" in source
