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
async def test_registry_execution_is_unchanged_without_agent_context(monkeypatch) -> None:
    calls = []

    async def original(name, arguments, **kwargs):
        calls.append((name, arguments, kwargs))
        return {"ok": True}

    monkeypatch.setattr(registry, "execute", original)
    result = await registry.execute("calculator", {"expression": "1+1"})\n
    assert result == {"ok": True}
    assert calls == [("calculator", {"expression": "1+1"}, {})]
