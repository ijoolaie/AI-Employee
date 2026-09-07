from uuid import uuid4

import pytest

from app.ai.tool_registry import registry
from app.services import agent_tool_governance


@pytest.mark.asyncio
async def test_agent_tool_context_is_tenant_and_instance_scoped() -> None:
    tenant_id = uuid4()
    instance_id = uuid4()

    assert agent_tool_governance._AGENT_CONTEXT.get() is None
    async with agent_tool_governance.agent_tool_context(
        tenant_id=tenant_id,
        agent_instance_id=instance_id,
    ):
        assert agent_tool_governance._AGENT_CONTEXT.get() == (tenant_id, instance_id)
    assert agent_tool_governance._AGENT_CONTEXT.get() is None


@pytest.mark.asyncio
async def test_registry_boundary_authorizes_agent_before_original_execute(monkeypatch) -> None:
    tenant_id = uuid4()
    instance_id = uuid4()
    calls = []
    authorization = []

    async def original(name, arguments, **kwargs):
        calls.append((name, arguments, kwargs))
        return {"ok": True}

    async def authorize(db, *, tenant_id, agent_instance_id, tool_name, required_permission, **kwargs):
        authorization.append((tenant_id, agent_instance_id, tool_name, required_permission))

    monkeypatch.setattr(registry, "execute", original)
    monkeypatch.setattr(agent_tool_governance, "_INSTALLED", False)
    monkeypatch.setattr(agent_tool_governance, "assert_agent_can_execute", authorize)
    agent_tool_governance.install()

    async with agent_tool_governance.agent_tool_context(
        tenant_id=tenant_id,
        agent_instance_id=instance_id,
    ):
        result = await registry.execute(
            "calculator",
            {"expression": "1+1"},
            db=object(),
            tenant_id=tenant_id,
        )

    assert result == {"ok": True}
    assert calls == [("calculator", {"expression": "1+1"}, {"db": calls[0][2]["db"], "tenant_id": tenant_id})]
    assert authorization == [(tenant_id, instance_id, "calculator", "run.execute")]
