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


def test_workforce_tool_resolves_to_explicit_catalog_operation():
    assert runtime.workforce_operation_for_tool("workforce_market_research") == (
        "ai_trader",
        "market_research",
    )
    assert runtime.workforce_operation_for_tool("calculator") is None


@pytest.mark.asyncio
async def test_workforce_tool_execution_rejects_wrong_role():
    tenant_id = uuid4()
    agent_id = uuid4()
    agent = SimpleNamespace(
        id=agent_id,
        tenant_id=tenant_id,
        configuration={"workforce_role_code": "ai_marketing_advertising_manager"},
    )

    class Result:
        def scalar_one_or_none(self):
            return agent

    class DB:
        async def execute(self, _query):
            return Result()

    with pytest.raises(ValidationAppError, match="not bound to the executing Agent role"):
        await runtime.assert_workforce_tool_execution(
            DB(),
            tenant_id=tenant_id,
            agent_instance_id=agent_id,
            tool_name="workforce_market_research",
        )

@pytest.mark.asyncio
async def test_workforce_tool_execution_scopes_agent_lookup_to_requested_tenant():
    tenant_id = uuid4()
    agent_id = uuid4()

    class Result:
        def scalar_one_or_none(self):
            return None

    class DB:
        async def execute(self, statement):
            # Guard the SQL predicate itself, not only the error returned by a mock.
            bound_values = statement.compile().params.values()
            assert tenant_id in bound_values
            assert agent_id in bound_values
            return Result()

    with pytest.raises(ValidationAppError, match="tenant-scoped AgentInstance"):
        await runtime.assert_workforce_tool_execution(
            DB(),
            tenant_id=tenant_id,
            agent_instance_id=agent_id,
            tool_name="workforce_market_research",
        )


@pytest.mark.asyncio
async def test_internal_manager_rejects_runtime_tenant_or_agent_identity_mismatch(monkeypatch):
    tenant_id = uuid4()
    manager_id = uuid4()
    agent = SimpleNamespace(
        id=manager_id,
        tenant_id=tenant_id,
        configuration={"workforce_role_code": "ai_internal_manager"},
    )
    # The active runtime belongs to a different tenant, despite the supplied Agent.
    monkeypatch.setattr(
        runtime,
        "current_agent_execution_context",
        lambda: (uuid4(), manager_id, uuid4(), None, None),
    )

    async def fail_if_delegation_checked(*_args, **_kwargs):
        raise AssertionError("delegation must not be checked for mismatched runtime identity")

    monkeypatch.setattr(runtime, "assert_operation_delegated", fail_if_delegation_checked)
    with pytest.raises(ValidationAppError, match="runtime identity mismatch"):
        await runtime.assert_workforce_operation(
            SimpleNamespace(),
            agent=agent,
            operation="assign_task",
        )


@pytest.mark.asyncio
async def test_internal_manager_requires_durable_run_before_delegation(monkeypatch):
    tenant_id = uuid4()
    manager_id = uuid4()
    agent = SimpleNamespace(
        id=manager_id,
        tenant_id=tenant_id,
        configuration={"workforce_role_code": "ai_internal_manager"},
    )
    monkeypatch.setattr(
        runtime,
        "current_agent_execution_context",
        lambda: (tenant_id, manager_id, None, None, None),
    )

    async def fail_if_delegation_checked(*_args, **_kwargs):
        raise AssertionError("delegation must not be checked without a durable Run identity")

    monkeypatch.setattr(runtime, "assert_operation_delegated", fail_if_delegation_checked)
    with pytest.raises(ValidationAppError, match="durable Run identity"):
        await runtime.assert_workforce_operation(
            SimpleNamespace(),
            agent=agent,
            operation="assign_task",
        )


@pytest.mark.asyncio
async def test_internal_manager_rejects_runtime_agent_identity_mismatch(monkeypatch):
    tenant_id = uuid4()
    manager_id = uuid4()
    agent = SimpleNamespace(
        id=manager_id,
        tenant_id=tenant_id,
        configuration={"workforce_role_code": "ai_internal_manager"},
    )
    # The tenant matches, but the active runtime is bound to a different Agent.
    monkeypatch.setattr(
        runtime,
        "current_agent_execution_context",
        lambda: (tenant_id, uuid4(), uuid4(), None, None),
    )

    async def fail_if_delegation_checked(*_args, **_kwargs):
        raise AssertionError("delegation must not be checked for mismatched runtime Agent identity")

    monkeypatch.setattr(runtime, "assert_operation_delegated", fail_if_delegation_checked)
    with pytest.raises(ValidationAppError, match="runtime identity mismatch"):
        await runtime.assert_workforce_operation(
            SimpleNamespace(),
            agent=agent,
            operation="assign_task",
        )

@pytest.mark.asyncio
async def test_approved_gated_workforce_tool_requires_exact_persisted_approval():
    from app.services.ai_workforce_roles import workforce_capability_contract_snapshot

    tenant_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    approval_id = uuid4()
    tool_call_id = "call_git_branch_1"
    arguments = {"branch_name": "agent/fix", "source_sha": "a" * 40}
    approval = SimpleNamespace(
        id=approval_id,
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="workforce_git_branch",
        tool_call_id=tool_call_id,
        status="approved",
        arguments=arguments,
    )
    agent = SimpleNamespace(
        id=agent_id,
        tenant_id=tenant_id,
        configuration={
            "workforce_role_code": "ai_software_developer",
            "workforce_capability_contract": workforce_capability_contract_snapshot("ai_software_developer"),
        },
    )

    class Result:
        def __init__(self, value):
            self.value = value

        def scalar_one_or_none(self):
            return self.value

    class DB:
        def __init__(self):
            self.calls = 0

        async def execute(self, statement):
            self.calls += 1
            params = statement.compile().params
            assert tenant_id in params.values()
            if self.calls == 1:
                assert agent_id in params.values()
                return Result(agent)
            assert approval_id in params.values()
            assert run_id in params.values()
            assert tool_call_id in params.values()
            assert "workforce_git_branch" in params.values()
            assert "approved" in params.values()
            return Result(approval)

    await runtime.assert_workforce_tool_execution(
        DB(),
        tenant_id=tenant_id,
        agent_instance_id=agent_id,
        tool_name="workforce_git_branch",
        approval_request_id=approval_id,
        run_id=run_id,
        tool_call_id=tool_call_id,
        arguments=arguments,
    )


@pytest.mark.asyncio
async def test_approved_gated_workforce_tool_rejects_argument_mismatch():
    from app.services.ai_workforce_roles import workforce_capability_contract_snapshot

    tenant_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    approval_id = uuid4()
    tool_call_id = "call_git_branch_2"
    approved_arguments = {"branch_name": "agent/approved", "source_sha": "b" * 40}
    changed_arguments = {"branch_name": "agent/changed", "source_sha": "b" * 40}
    approval = SimpleNamespace(
        id=approval_id,
        tenant_id=tenant_id,
        run_id=run_id,
        tool_name="workforce_git_branch",
        tool_call_id=tool_call_id,
        status="approved",
        arguments=approved_arguments,
    )
    agent = SimpleNamespace(
        id=agent_id,
        tenant_id=tenant_id,
        configuration={
            "workforce_role_code": "ai_software_developer",
            "workforce_capability_contract": workforce_capability_contract_snapshot("ai_software_developer"),
        },
    )

    class Result:
        def __init__(self, value):
            self.value = value

        def scalar_one_or_none(self):
            return self.value

    class DB:
        def __init__(self):
            self.calls = 0

        async def execute(self, statement):
            self.calls += 1
            if self.calls == 1:
                return Result(agent)
            return Result(approval)

    with pytest.raises(ValidationAppError, match="does not match"):
        await runtime.assert_workforce_tool_execution(
            DB(),
            tenant_id=tenant_id,
            agent_instance_id=agent_id,
            tool_name="workforce_git_branch",
            approval_request_id=approval_id,
            run_id=run_id,
            tool_call_id=tool_call_id,
            arguments=changed_arguments,
        )
