"""API-boundary acceptance coverage for canonical Unified Execution."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import work_items
from app.models.work_item import ExecutorType, WorkItemStatus


class FakeDB:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


@pytest.mark.asyncio
async def test_human_assignment_dispatch_and_terminal_result_are_exposed(monkeypatch):
    tenant_id = uuid4()
    user_id = uuid4()
    human_id = uuid4()
    work_item_id = uuid4()
    db = FakeDB()
    calls = {}

    item = SimpleNamespace(
        id=work_item_id,
        tenant_id=tenant_id,
        executor_type=ExecutorType.HUMAN,
        executor_id=None,
        status=WorkItemStatus.READY,
        output_data={},
    )

    async def fake_get_work_item(*_args, **_kwargs):
        return item

    class FakeService:
        def __init__(self, _db, **_kwargs):
            pass

        def assign_human(self, received, executor_id):
            calls["assigned"] = (received, executor_id)
            received.executor_id = executor_id
            received.executor_type = ExecutorType.HUMAN
            received.status = WorkItemStatus.ASSIGNED

        async def dispatch(self, received):
            calls["dispatched"] = received
            received.status = WorkItemStatus.RUNNING
            received.output_data = {"correlation_id": str(received.id)}
            return SimpleNamespace(work_item=received, dispatched=True, waiting_for_approval=False)

    async def fake_record(*_args, **kwargs):
        calls.setdefault("audit", []).append(kwargs)

    monkeypatch.setattr(work_items, "_get_work_item", fake_get_work_item)
    monkeypatch.setattr(work_items, "UnifiedExecutionService", FakeService)
    monkeypatch.setattr(work_items, "record_execution_event", fake_record)

    user = SimpleNamespace(tenant_id=tenant_id, user_id=user_id)
    assigned = await work_items.assign_human(
        work_item_id,
        payload=SimpleNamespace(executor_id=human_id),
        db=db,
        current_user=user,
    )
    dispatched = await work_items.dispatch(work_item_id, db=db, current_user=user)

    assert assigned.status == WorkItemStatus.ASSIGNED.value
    assert dispatched.status == WorkItemStatus.RUNNING.value
    assert calls["assigned"] == (item, human_id)
    assert calls["dispatched"] is item
    assert calls["audit"][0]["action"] == "work_item.assigned"
    assert calls["audit"][1]["action"] == "work_item.dispatched"


@pytest.mark.asyncio
async def test_approval_required_dispatch_is_exposed_as_waiting_and_audited(monkeypatch):
    tenant_id = uuid4()
    work_item_id = uuid4()
    db = FakeDB()
    calls = {}

    item = SimpleNamespace(
        id=work_item_id,
        tenant_id=tenant_id,
        executor_type=ExecutorType.HUMAN,
        status=WorkItemStatus.ASSIGNED,
        output_data={},
    )

    async def fake_get_work_item(*_args, **_kwargs):
        return item

    class FakeService:
        def __init__(self, _db, **_kwargs):
            pass

        async def dispatch(self, received):
            received.status = WorkItemStatus.WAITING_APPROVAL
            return SimpleNamespace(work_item=received, dispatched=False, waiting_for_approval=True)

    async def fake_record(*_args, **kwargs):
        calls["audit"] = kwargs

    monkeypatch.setattr(work_items, "_get_work_item", fake_get_work_item)
    monkeypatch.setattr(work_items, "UnifiedExecutionService", FakeService)
    monkeypatch.setattr(work_items, "record_execution_event", fake_record)

    result = await work_items.dispatch(
        work_item_id,
        db=db,
        current_user=SimpleNamespace(tenant_id=tenant_id, user_id=uuid4()),
    )

    assert result.waiting_for_approval is True
    assert result.dispatched is False
    assert result.status == WorkItemStatus.WAITING_APPROVAL.value
    assert calls["audit"]["action"] == "work_item.waiting_approval"
    assert calls["audit"]["status"] == "pending"


@pytest.mark.asyncio
async def test_agent_dispatch_failure_is_audited_truthfully(monkeypatch):
    tenant_id = uuid4()
    work_item_id = uuid4()
    db = FakeDB()
    calls = {}

    item = SimpleNamespace(
        id=work_item_id,
        tenant_id=tenant_id,
        executor_type=ExecutorType.AGENT,
        status=WorkItemStatus.FAILED,
        output_data={"error": "executor unavailable"},
    )

    async def fake_get_work_item(*_args, **_kwargs):
        return item

    class FakeAdapter:
        def __init__(self, _db):
            calls["adapter"] = True

    class FakeService:
        def __init__(self, _db, *, agent_executor=None, human_executor=None):
            calls["service_agent_executor"] = agent_executor
            calls["service_human_executor"] = human_executor

        async def dispatch(self, received):
            return SimpleNamespace(work_item=received, dispatched=False, waiting_for_approval=False)

    async def fake_record(*_args, **kwargs):
        calls["audit"] = kwargs

    monkeypatch.setattr(work_items, "_get_work_item", fake_get_work_item)
    monkeypatch.setattr(work_items, "AgentExecutionAdapter", FakeAdapter)
    monkeypatch.setattr(work_items, "UnifiedExecutionService", FakeService)
    monkeypatch.setattr(work_items, "record_execution_event", fake_record)

    result = await work_items.dispatch(
        work_item_id,
        db=db,
        current_user=SimpleNamespace(tenant_id=tenant_id, user_id=uuid4()),
    )

    assert isinstance(calls["service_agent_executor"], FakeAdapter)
    assert calls["service_human_executor"] is None
    assert result.status == WorkItemStatus.FAILED.value
    assert calls["audit"]["action"] == "work_item.execution_failed"
    assert calls["audit"]["status"] == "failure"
