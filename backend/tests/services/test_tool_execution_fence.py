from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai.tool_registry import RegisteredTool, registry
from app.services import agent_tool_governance, license_service, tool_execution_fence


class _DB:
    async def execute(self, _query):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: []))

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_side_effect_tool_has_durable_fence_before_handler_and_blocks_replay(monkeypatch):
    tenant_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    db = _DB()
    calls = []
    fence_ids = []
    fence_attempts = 0

    async def handler(arguments, **kwargs):
        calls.append(arguments)
        return {"ok": True}

    name = f"test_side_effect_fence_{uuid4().hex[:8]}"
    registry.register(
        RegisteredTool(
            name=name,
            description="test",
            input_schema={"type": "object", "additionalProperties": False},
            handler=handler,
            side_effects=True,
            external_side_effects=True,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    async def fake_authorize(*args, **kwargs):
        return None

    async def fake_begin(**kwargs):
        nonlocal fence_attempts
        fence_attempts += 1
        if fence_attempts > 1:
            from app.core.exceptions import ValidationAppError

            raise ValidationAppError(
                "Tool execution already crossed the side-effect boundary"
            )
        fence_id = uuid4()
        fence_ids.append(fence_id)
        return fence_id

    async def fake_complete(*args, **kwargs):
        return None

    async def fake_unknown(*args, **kwargs):
        return None

    async def fake_entitlement(*args, **kwargs):
        return None

    monkeypatch.setattr(license_service, "assert_feature_entitlement", fake_entitlement)
    monkeypatch.setattr(agent_tool_governance, "assert_authorized", fake_authorize)
    monkeypatch.setattr(
        tool_execution_fence,
        "begin_tool_execution_fence",
        fake_begin,
    )
    monkeypatch.setattr(
        tool_execution_fence,
        "complete_tool_execution_fence",
        fake_complete,
    )
    monkeypatch.setattr(
        tool_execution_fence,
        "mark_tool_execution_unknown",
        fake_unknown,
    )

    try:
        async with agent_tool_governance.agent_tool_context(
            tenant_id=tenant_id,
            agent_instance_id=agent_id,
            run_id=run_id,
        ):
            result = await registry.execute(
                name,
                {},
                permissions={"run.execute"},
                db=db,
                tenant_id=tenant_id,
                tool_call_id="call-1",
            )

        assert result == {"ok": True}
        assert calls == [{}]
        assert len(fence_ids) == 1

        with pytest.raises(Exception, match="already crossed"):
            async with agent_tool_governance.agent_tool_context(
                tenant_id=tenant_id,
                agent_instance_id=agent_id,
                run_id=run_id,
            ):
                await registry.execute(
                    name,
                    {},
                    permissions={"run.execute"},
                    db=db,
                    tenant_id=tenant_id,
                    tool_call_id="call-1",
                )

        assert calls == [{}]
        assert fence_attempts == 2
    finally:
        registry._tools.pop(name, None)
