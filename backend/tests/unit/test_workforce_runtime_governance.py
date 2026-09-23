from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.services import workforce_runtime_governance as runtime


@pytest.mark.asyncio
async def test_specialized_role_allows_only_catalog_routine_operation(monkeypatch):
    agent = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        configuration={"workforce_role_code": "ai_trader"},
    )
    db = SimpleNamespace()

    await runtime.assert_workforce_operation(
        db,
        agent=agent,
        operation="market_research",
    )

    with pytest.raises(ValidationAppError, match="Human approval"):
        await runtime.assert_workforce_operation(
            db,
            agent=agent,
            operation="order_execution",
        )

    with pytest.raises(ValidationAppError, match="not authorized"):
        await runtime.assert_workforce_operation(
            db,
            agent=agent,
            operation="create_visual_asset",
        )


@pytest.mark.asyncio
async def test_internal_manager_requires_runtime_and_ceo_delegation(monkeypatch):
    tenant_id = uuid4()
    manager_id = uuid4()
    agent = SimpleNamespace(
        id=manager_id,
        tenant_id=tenant_id,
        configuration={"workforce_role_code": "ai_internal_manager"},
    )

    monkeypatch.setattr(runtime, "current_agent_execution_context", lambda: None)
    with pytest.raises(ValidationAppError, match="runtime context"):
        await runtime.assert_workforce_operation(
            SimpleNamespace(),
            agent=agent,
            operation="assign_task",
        )

    monkeypatch.setattr(
        runtime,
        "current_agent_execution_context",
        lambda: (tenant_id, manager_id, uuid4(), None, None),
    )

    called = {}

    async def delegated(*args, **kwargs):
        called.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(runtime, "assert_operation_delegated", delegated)
    await runtime.assert_workforce_operation(
        SimpleNamespace(),
        agent=agent,
        operation="assign_task",
    )
    assert called["manager_agent_instance_id"] == manager_id


@pytest.mark.asyncio
async def test_unknown_or_missing_role_fails_closed():
    agent = SimpleNamespace(id=uuid4(), tenant_id=uuid4(), configuration={})
    with pytest.raises(ValidationAppError, match="role identity"):
        await runtime.assert_workforce_operation(
            SimpleNamespace(),
            agent=agent,
            operation="market_research",
        )

    agent.configuration["workforce_role_code"] = "ai_unknown"
    with pytest.raises(ValidationAppError, match="Unknown workforce role"):
        await runtime.assert_workforce_operation(
            SimpleNamespace(),
            agent=agent,
            operation="market_research",
        )


@pytest.mark.asyncio
async def test_stale_workforce_capability_contract_fails_closed():
    agent = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        configuration={
            "workforce_role_code": "ai_trader",
            "workforce_capability_contract": [
                {
                    "operation": "market_research",
                    "capability_code": "workforce.market_research",
                    "tool_names": ["calculator"],
                    "required_permissions": ["run.execute"],
                    "approval_required": False,
                }
            ],
        },
    )
    with pytest.raises(ValidationAppError, match="capability contract is stale"):
        await runtime.assert_workforce_operation(
            SimpleNamespace(),
            agent=agent,
            operation="market_research",
        )
