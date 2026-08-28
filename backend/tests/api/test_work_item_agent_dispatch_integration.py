"""Integration-boundary tests for the agent WorkItem dispatch endpoint.

These tests exercise the endpoint's tenant boundary and execution-service wiring
without inventing a second database fixture stack.
"""
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import work_items


@pytest.mark.asyncio
async def test_agent_dispatch_uses_tenant_scoped_executor(monkeypatch):
    tenant_id = uuid4()
    work_item_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    calls = {}

    work_item = SimpleNamespace(
        id=work_item_id,
        tenant_id=tenant_id,
        execution_type="agent",
        assigned_agent_instance_id=agent_id,
        status="pending",
        output_data=None,
    )
    agent = SimpleNamespace(id=agent_id, tenant_id=tenant_id)

    async def fake_get_work_item(db, item_id, requested_tenant_id):
        calls["work_item_lookup"] = (item_id, requested_tenant_id)
        return work_item

    async def fake_get_agent(db, agent_id_value, requested_tenant_id):
        calls["agent_lookup"] = (agent_id_value, requested_tenant_id)
        return agent

    class FakeExecutor:
        def __init__(self, db):
            calls["executor_db"] = db

        async def dispatch(self, item, agent_value):
            calls["dispatch"] = (item, agent_value)
            return {"run_id": str(run_id)}

    monkeypatch.setattr(work_items, "_get_work_item", fake_get_work_item)
    monkeypatch.setattr(work_items, "_get_agent_instance", fake_get_agent)
    monkeypatch.setattr(work_items, "UnifiedExecutionService", FakeExecutor)

    result = await work_items.dispatch_work_item(
        work_item_id,
        db=object(),
        tenant_id=tenant_id,
        user_id=uuid4(),
        idempotency_key=None,
    )

    assert calls["work_item_lookup"] == (work_item_id, tenant_id)
    assert calls["agent_lookup"] == (agent_id, tenant_id)
    assert calls["dispatch"] == (work_item, agent)
    assert result["run_id"] == str(run_id)


@pytest.mark.asyncio
async def test_agent_dispatch_rejects_cross_tenant_agent_before_executor(monkeypatch):
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    work_item_id = uuid4()
    agent_id = uuid4()
    calls = {"executor": 0}

    work_item = SimpleNamespace(
        id=work_item_id,
        tenant_id=tenant_id,
        execution_type="agent",
        assigned_agent_instance_id=agent_id,
        status="pending",
        output_data=None,
    )
    foreign_agent = SimpleNamespace(id=agent_id, tenant_id=other_tenant_id)

    async def fake_get_work_item(db, item_id, requested_tenant_id):
        return work_item

    async def fake_get_agent(db, agent_id_value, requested_tenant_id):
        return foreign_agent

    class ForbiddenExecutor:
        def __init__(self, db):
            calls["executor"] += 1

    monkeypatch.setattr(work_items, "_get_work_item", fake_get_work_item)
    monkeypatch.setattr(work_items, "_get_agent_instance", fake_get_agent)
    monkeypatch.setattr(work_items, "UnifiedExecutionService", ForbiddenExecutor)

    with pytest.raises(Exception) as exc:
        await work_items.dispatch_work_item(
            work_item_id,
            db=object(),
            tenant_id=tenant_id,
            user_id=uuid4(),
            idempotency_key=None,
        )

    assert "tenant" in str(exc.value).lower() or "not found" in str(exc.value).lower()
    assert calls["executor"] == 0
