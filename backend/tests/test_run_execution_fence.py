from pathlib import Path


def test_run_worker_uses_locked_execution_fence():
    worker = Path(__file__).parents[1] / "app" / "workers" / "run_worker.py"
    source = worker.read_text(encoding="utf-8")

    assert "from app.services.run_execution_fence import execute_run_locked" in source
    assert "execute_run_locked(db, run_id=parsed_run_id)" in source
    assert "run_service.execute_run(db, run_id=parsed_run_id)" not in source


def test_run_execution_fence_locks_workitem_lineage_before_run():
    fence = Path(__file__).parents[1] / "app" / "services" / "run_execution_fence.py"
    source = fence.read_text(encoding="utf-8")

    assert "from app.models.work_item import WorkItem" in source
    assert "async def _lock_work_item_lineage" in source
    assert "select(WorkItem.id, WorkItem.parent_work_item_id)" in source
    assert "for item_id in reversed(lineage_ids)" in source
    assert "select(WorkItem)" in source
    assert "select(Run).where(Run.id == run_id).with_for_update()" in source
    assert source.index("select(WorkItem)") < source.index("select(Run).where(Run.id == run_id).with_for_update()")


import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ConflictError
from app.services import audit_service, billing_service, run_service
from app.services.run_execution_fence import execute_run_locked


@pytest.mark.asyncio
async def test_run_execution_fence_fails_closed_when_entitlement_is_revoked(monkeypatch):
    run = SimpleNamespace(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        work_item_id=None,
        status="pending",
        error_message=None,
        completed_at=None,
    )
    row = SimpleNamespace(scalar_one_or_none=lambda: run)
    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[row, row])

    monkeypatch.setattr(
        billing_service,
        "assert_run_execution_entitlement",
        AsyncMock(side_effect=ConflictError("Subscription is not active")),
    )
    monkeypatch.setattr(audit_service, "record", AsyncMock())
    execute = AsyncMock()
    monkeypatch.setattr(run_service, "execute_run", execute)

    result = await execute_run_locked(db, run_id=run.id)

    assert result is run
    assert run.status == "failed"
    assert run.error_message == "Subscription is not active"
    execute.assert_not_awaited()
    assert db.flush.await_count == 1


def test_run_execution_fence_requires_entitlement_before_run_service():
    fence = Path(__file__).parents[1] / "app" / "services" / "run_execution_fence.py"
    source = fence.read_text(encoding="utf-8")

    assert "await billing_service.assert_run_execution_entitlement(" in source
    assert source.index("assert_run_execution_entitlement") < source.rindex("run_service.execute_run(db, run_id=run_id)")
