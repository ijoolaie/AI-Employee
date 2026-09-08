from uuid import uuid4

import pytest

from app.ai.tool_registry import registry
from app.core.exceptions import ValidationAppError
from app.services import agent_tool_governance


@pytest.mark.asyncio
async def test_agent_tool_context_is_tenant_instance_and_run_scoped() -> None:
    tenant_id, instance_id, run_id = uuid4(), uuid4(), uuid4()
    assert agent_tool_governance._AGENT_CONTEXT.get() is None
    async with agent_tool_governance.agent_tool_context(tenant_id=tenant_id, agent_instance_id=instance_id, run_id=run_id):
        assert agent_tool_governance._AGENT_CONTEXT.get() == (tenant_id, instance_id, run_id)
    assert agent_tool_governance._AGENT_CONTEXT.get() is None


@pytest.mark.asyncio
async def test_registry_boundary_authorizes_agent_before_original_execute(monkeypatch) -> None:
    tenant_id, instance_id, run_id = uuid4(), uuid4(), uuid4()
    db = object()
    calls, authorization = [], []

    async def original(name, arguments, **kwargs):
        calls.append((name, arguments, kwargs))
        return {"ok": True}

    async def authorize(_db, request):
        authorization.append((request.tenant_id, request.agent_instance_id, request.tool_name, request.required_permission, request.run_id))

    monkeypatch.setattr(registry, "execute", original)
    monkeypatch.setattr(agent_tool_governance, "_INSTALLED", False)
    monkeypatch.setattr(agent_tool_governance, "assert_authorized", authorize)
    agent_tool_governance.install()

    async with agent_tool_governance.agent_tool_context(tenant_id=tenant_id, agent_instance_id=instance_id, run_id=run_id):
        result = await registry.execute("calculator", {"expression": "1+1"}, db=db, tenant_id=tenant_id)

    assert result == {"ok": True}
    assert authorization == [(tenant_id, instance_id, "calculator", "run.execute", run_id)]
    assert calls[0][2]["db"] is db
    assert calls[0][2]["tenant_id"] == tenant_id
    assert calls[0][2]["approval_granted"] is False


@pytest.mark.asyncio
async def test_registry_boundary_rejects_cross_tenant_context(monkeypatch) -> None:
    tenant_id, other_tenant_id, instance_id, run_id = uuid4(), uuid4(), uuid4(), uuid4()
    calls = []

    async def original(*args, **kwargs):
        calls.append((args, kwargs))
        return {"ok": True}

    monkeypatch.setattr(registry, "execute", original)
    monkeypatch.setattr(agent_tool_governance, "_INSTALLED", False)
    agent_tool_governance.install()

    async with agent_tool_governance.agent_tool_context(tenant_id=tenant_id, agent_instance_id=instance_id, run_id=run_id):
        with pytest.raises(ValidationAppError, match="tenant context mismatch"):
            await registry.execute("calculator", {"expression": "1+1"}, db=object(), tenant_id=other_tenant_id)
    assert calls == []


@pytest.mark.asyncio
async def test_approval_boolean_alone_cannot_bypass_agent_boundary(monkeypatch) -> None:
    tenant_id, instance_id, run_id = uuid4(), uuid4(), uuid4()
    calls = []

    class EmptyResult:
        def scalars(self): return self
        def all(self): return []

    class Db:
        async def execute(self, _statement): return EmptyResult()

    async def original(*args, **kwargs):
        calls.append((args, kwargs))
        return {"ok": True}

    monkeypatch.setattr(registry, "execute", original)
    monkeypatch.setattr(agent_tool_governance, "_INSTALLED", False)
    agent_tool_governance.install()

    async with agent_tool_governance.agent_tool_context(tenant_id=tenant_id, agent_instance_id=instance_id, run_id=run_id):
        with pytest.raises(ValidationAppError, match="Human approval required"):
            await registry.execute("send_email", {"to": ["allowed@example.com"], "subject": "x", "body": "y"}, db=Db(), tenant_id=tenant_id, approval_granted=True)
    assert calls == []
