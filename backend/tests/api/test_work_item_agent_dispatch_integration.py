"""Integration-boundary tests for the agent WorkItem execution API."""
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import work_items
from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.unified_execution import ExecutionError


class FakeDB:
    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def get(self, model, object_id):
        return None


@pytest.mark.asyncio
async def test_agent_dispatch_wires_adapter_into_execution_service(monkeypatch):
    tenant_id = uuid4()
    work_item_id = uuid4()
    run_id = uuid4()
    db = FakeDB()
    calls = {}

    work_item = SimpleNamespace(
        id=work_item_id,
        tenant_id=tenant_id,
        executor_type=ExecutorType.AGENT,
        status=WorkItemStatus.READY,
        output_data={"run_id": str(run_id)},
    )

    async def fake_get_work_item(db_value, item_id, requested_tenant_id):
        calls["lookup"] = (db_value, item_id, requested_tenant_id)
        return work_item

    class FakeAdapter:
        def __init__(self, db_value):
            calls["adapter_db"] = db_value

    class FakeService:
        def __init__(self, db_value, *, agent_executor=None, human_executor=None):
            calls["service"] = (db_value, agent_executor, human_executor)

        async def dispatch(self, item):
            calls["dispatch"] = item
            return SimpleNamespace(work_item=item, dispatched=True, waiting_for_approval=False)

    async def fake_record(*args, **kwargs):
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

    assert calls["lookup"] == (db, work_item_id, tenant_id)
    assert isinstance(calls["service"][1], FakeAdapter)
    assert calls["service"][2] is None
    assert calls["adapter_db"] is db
    assert calls["dispatch"] is work_item
    assert result.work_item_id == work_item_id
    assert result.dispatched is True


@pytest.mark.asyncio
async def test_agent_assignment_rejects_cross_tenant_agent_before_execution(monkeypatch):
    tenant_id = uuid4()
    work_item_id = uuid4()
    agent_id = uuid4()
    db = FakeDB()
    calls = {"service": 0}

    async def fake_assign_work_item(*, tenant_id, work_item_id, agent_instance_id, db):
        assert tenant_id is not None
        assert work_item_id == work_item_id
        assert agent_instance_id == agent_id
        calls["service"] += 1
        raise ExecutionError("agent instance not found")

    monkeypatch.setattr(work_items, "assign_agent_work_item", fake_assign_work_item)

    with pytest.raises(work_items.HTTPException) as exc:
        await work_items.assign_agent(
            work_item_id,
            payload=SimpleNamespace(agent_instance_id=agent_id),
            db=db,
            current_user=SimpleNamespace(tenant_id=tenant_id, user_id=uuid4()),
        )

    assert exc.value.status_code == 404
    assert calls["service"] == 1
