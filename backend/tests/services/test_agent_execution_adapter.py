from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import agent_execution_adapter


@pytest.mark.asyncio
async def test_agent_adapter_creates_run_from_resolved_employee_version(monkeypatch):
    tenant_id = uuid4()
    agent_id = uuid4()
    definition_id = uuid4()
    employee_id = uuid4()
    version_id = uuid4()
    run_id = uuid4()
    requester_id = uuid4()
    calls = {}

    work_item = SimpleNamespace(
        tenant_id=tenant_id,
        input_data={"task": "triage"},
        requester_id=requester_id,
    )
    agent = SimpleNamespace(id=agent_id)
    instance = SimpleNamespace(id=agent_id)
    definition = SimpleNamespace(id=definition_id)
    version = SimpleNamespace(id=version_id, employee_id=employee_id)
    run = SimpleNamespace(id=run_id, agent_instance_id=None)

    async def authorize(db, request):
        calls["authorize"] = (db, request)

    async def resolve(db, *, tenant_id, agent_instance_id):
        calls["resolve"] = (db, tenant_id, agent_instance_id)
        return instance, definition, version

    async def create(db, **kwargs):
        calls["create"] = (db, kwargs)
        return run

    monkeypatch.setattr(agent_execution_adapter, "assert_authorized", authorize)
    monkeypatch.setattr(agent_execution_adapter, "resolve_employee_version", resolve)
    monkeypatch.setattr(agent_execution_adapter, "create_run", create)

    class _DB:
        async def flush(self):
            return None

    db = _DB()
    result = await agent_execution_adapter.AgentExecutionAdapter(db).dispatch(work_item, agent)

    assert calls["authorize"][0] is db
    assert calls["authorize"][1].tenant_id == tenant_id
    assert calls["authorize"][1].agent_instance_id == agent_id
    assert calls["authorize"][1].action == "run.execute"
    assert calls["resolve"] == (db, tenant_id, agent_id)
    assert calls["create"][1] == {
        "tenant_id": tenant_id,
        "employee_id": employee_id,
        "employee_version_id": version_id,
        "input_data": {"task": "triage"},
        "created_by": requester_id,
    }
    assert run.agent_instance_id == agent_id
    assert result == {
        "run_id": str(run_id),
        "executor_type": "agent",
        "agent_instance_id": str(agent_id),
        "agent_definition_id": str(definition_id),
        "employee_id": str(employee_id),
        "employee_version_id": str(version_id),
    }


@pytest.mark.asyncio
async def test_agent_adapter_denies_before_creating_run_when_authority_changes(monkeypatch):
    tenant_id = uuid4()
    agent_id = uuid4()
    calls = []

    async def authorize(_db, _request):
        calls.append("authorize")
        raise RuntimeError("agent authority revoked")

    async def resolve(*_args, **_kwargs):
        raise AssertionError("employee resolution must not run after authorization denial")

    async def create(*_args, **_kwargs):
        raise AssertionError("Run must not be created after authorization denial")

    monkeypatch.setattr(agent_execution_adapter, "assert_authorized", authorize)
    monkeypatch.setattr(agent_execution_adapter, "resolve_employee_version", resolve)
    monkeypatch.setattr(agent_execution_adapter, "create_run", create)

    work_item = SimpleNamespace(tenant_id=tenant_id, input_data={}, requester_id=None)
    agent = SimpleNamespace(id=agent_id)

    with pytest.raises(RuntimeError, match="authority revoked"):
        await agent_execution_adapter.AgentExecutionAdapter(object()).dispatch(work_item, agent)

    assert calls == ["authorize"]


@pytest.mark.asyncio
async def test_agent_adapter_does_not_bypass_tenant_scoped_resolver(monkeypatch):
    tenant_id = uuid4()
    agent_id = uuid4()
    seen = {}

    async def authorize(*_args, **_kwargs):
        return None

    async def resolve(db, *, tenant_id, agent_instance_id):
        seen["tenant_id"] = tenant_id
        seen["agent_instance_id"] = agent_instance_id
        raise RuntimeError("tenant-scoped resolution rejected")

    async def create(*_args, **_kwargs):
        raise AssertionError("Run must not be created after resolver rejection")

    monkeypatch.setattr(agent_execution_adapter, "assert_authorized", authorize)
    monkeypatch.setattr(agent_execution_adapter, "resolve_employee_version", resolve)
    monkeypatch.setattr(agent_execution_adapter, "create_run", create)

    work_item = SimpleNamespace(tenant_id=tenant_id, input_data={}, requester_id=None)
    agent = SimpleNamespace(id=agent_id)

    with pytest.raises(RuntimeError, match="tenant-scoped"):
        await agent_execution_adapter.AgentExecutionAdapter(object()).dispatch(work_item, agent)

    assert seen == {"tenant_id": tenant_id, "agent_instance_id": agent_id}
