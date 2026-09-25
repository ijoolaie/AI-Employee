"""API-boundary coverage for WorkItem cancel and retry lifecycle mutations."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import work_items
from app.models.work_item import WorkItemStatus
from app.services.unified_execution import ExecutionError


class FakeDB:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


@pytest.mark.asyncio
async def test_cancel_records_audit_and_returns_cancelled_state(monkeypatch):
    tenant_id = uuid4()
    work_item_id = uuid4()
    actor_id = uuid4()
    db = FakeDB()
    item = SimpleNamespace(
        id=work_item_id,
        tenant_id=tenant_id,
        status=WorkItemStatus.RUNNING,
    )
    calls = {}

    async def fake_get_work_item(*_args, **_kwargs):
        return item

    class FakeService:
        def __init__(self, _db):
            pass

        def cancel(self, received):
            received.status = WorkItemStatus.CANCELLED
            return received

    async def fake_record(*_args, **kwargs):
        calls["audit"] = kwargs

    monkeypatch.setattr(work_items, "_get_work_item", fake_get_work_item)
    monkeypatch.setattr(work_items, "UnifiedExecutionService", FakeService)
    monkeypatch.setattr(work_items, "record_execution_event", fake_record)

    result = await work_items.cancel(
        work_item_id,
        db=db,
        current_user=SimpleNamespace(tenant_id=tenant_id, user_id=actor_id),
    )

    assert result.status == WorkItemStatus.CANCELLED.value
    assert db.commits == 1
    assert calls["audit"]["action"] == "work_item.cancelled"
    assert calls["audit"]["actor_id"] == actor_id
    assert calls["audit"]["work_item_id"] == work_item_id


@pytest.mark.asyncio
async def test_retry_records_audit_and_increments_retry_count(monkeypatch):
    tenant_id = uuid4()
    work_item_id = uuid4()
    actor_id = uuid4()
    db = FakeDB()
    item = SimpleNamespace(
        id=work_item_id,
        tenant_id=tenant_id,
        status=WorkItemStatus.FAILED,
        policy_context={"retry_count": 1},
    )
    calls = {}

    async def fake_get_work_item(*_args, **_kwargs):
        return item

    class FakeService:
        def __init__(self, _db):
            pass

        def retry(self, received):
            received.policy_context["retry_count"] += 1
            received.status = WorkItemStatus.ASSIGNED
            return received

    async def fake_record(*_args, **kwargs):
        calls["audit"] = kwargs

    monkeypatch.setattr(work_items, "_get_work_item", fake_get_work_item)
    monkeypatch.setattr(work_items, "UnifiedExecutionService", FakeService)
    monkeypatch.setattr(work_items, "record_execution_event", fake_record)

    result = await work_items.retry(
        work_item_id,
        db=db,
        current_user=SimpleNamespace(tenant_id=tenant_id, user_id=actor_id),
    )

    assert result.status == WorkItemStatus.ASSIGNED.value
    assert item.policy_context["retry_count"] == 2
    assert db.commits == 1
    assert calls["audit"]["action"] == "work_item.retry"
    assert calls["audit"]["actor_id"] == actor_id
    assert calls["audit"]["resource_id"] == work_item_id
    assert calls["audit"]["metadata"]["retry_count"] == 2


@pytest.mark.asyncio
async def test_cancel_conflict_rolls_back_without_audit(monkeypatch):
    tenant_id = uuid4()
    work_item_id = uuid4()
    db = FakeDB()
    item = SimpleNamespace(
        id=work_item_id,
        tenant_id=tenant_id,
        status=WorkItemStatus.SUCCEEDED,
    )
    calls = {"audit": 0}

    async def fake_get_work_item(*_args, **_kwargs):
        return item

    class FakeService:
        def __init__(self, _db):
            pass

        def cancel(self, _received):
            raise ExecutionError("terminal work item cannot be cancelled")

    async def fake_record(*_args, **_kwargs):
        calls["audit"] += 1

    monkeypatch.setattr(work_items, "_get_work_item", fake_get_work_item)
    monkeypatch.setattr(work_items, "UnifiedExecutionService", FakeService)
    monkeypatch.setattr(work_items, "record_execution_event", fake_record)

    with pytest.raises(work_items.HTTPException) as exc_info:
        await work_items.cancel(
            work_item_id,
            db=db,
            current_user=SimpleNamespace(tenant_id=tenant_id, user_id=uuid4()),
        )

    assert exc_info.value.status_code == 409
    assert db.rollbacks == 1
    assert db.commits == 0
    assert calls["audit"] == 0
