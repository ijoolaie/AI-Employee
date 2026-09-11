from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, ValidationAppError
from app.models.agent_kill_switch import AgentKillScope, AgentKillSwitch
from app.services import agent_kill_switch_service


@pytest.mark.asyncio
async def test_active_agent_kill_switch_blocks_execution():
    tenant_id, agent_id = uuid4(), uuid4()
    switch = AgentKillSwitch(
        id=uuid4(), tenant_id=tenant_id, agent_instance_id=agent_id,
        scope=AgentKillScope.AGENT, active=True, reason="incident",
        correlation_id="corr-1",
    )

    class Scalars:
        def first(self):
            return switch

    class Result:
        def scalars(self):
            return Scalars()

    class Db:
        async def execute(self, statement):
            return Result()

    with pytest.raises(ValidationAppError, match="emergency kill switch"):
        await agent_kill_switch_service.assert_not_killed(Db(), tenant_id=tenant_id, agent_instance_id=agent_id)


@pytest.mark.asyncio
async def test_kill_switch_scope_precedence_is_fail_closed():
    tenant_id, agent_id = uuid4(), uuid4()
    calls = []

    class Result:
        def scalars(self):
            class Scalars:
                def first(self):
                    return AgentKillSwitch(
                        id=uuid4(), scope=AgentKillScope.TENANT, tenant_id=tenant_id,
                        active=True, reason="tenant incident", correlation_id="corr-2",
                    )
            return Scalars()

    class Db:
        async def execute(self, statement):
            calls.append(statement)
            return Result()

    with pytest.raises(ValidationAppError, match="emergency kill switch"):
        await agent_kill_switch_service.assert_not_killed(Db(), tenant_id=tenant_id, agent_instance_id=agent_id)
    assert calls


@pytest.mark.asyncio
async def test_assert_not_killed_serializes_all_kill_switch_scopes_before_check():
    tenant_id, agent_id = uuid4(), uuid4()
    statements = []

    class Scalars:
        def first(self):
            return None

    class Result:
        def scalars(self):
            return Scalars()

    class Db:
        async def execute(self, statement):
            statements.append(str(statement))
            return Result()

    await agent_kill_switch_service.assert_not_killed(Db(), tenant_id=tenant_id, agent_instance_id=agent_id)

    assert len(statements) == 4
    assert all("pg_advisory_xact_lock" in statement for statement in statements[:3])
    assert "FOR UPDATE" in statements[3]


@pytest.mark.asyncio
async def test_agent_kill_switch_rejects_cross_tenant_target():
    tenant_id, other_tenant = uuid4(), uuid4()
    agent_id = uuid4()

    class Result:
        def scalar_one_or_none(self):
            return None

    class Db:
        async def execute(self, statement):
            return Result()

    with pytest.raises(ValidationAppError, match="does not belong to tenant"):
        await agent_kill_switch_service.assert_kill(
            Db(),
            scope=AgentKillScope.AGENT,
            reason="incident",
            asserted_by=uuid4(),
            tenant_id=tenant_id,
            agent_instance_id=agent_id,
        )


@pytest.mark.asyncio
async def test_agent_kill_switch_assertion_serializes_before_check():
    tenant_id, agent_id = uuid4(), uuid4()
    existing = AgentKillSwitch(
        id=uuid4(), tenant_id=tenant_id, agent_instance_id=agent_id,
        scope=AgentKillScope.AGENT, active=True, reason="already active",
        correlation_id="corr-3",
    )
    statements = []

    class Result:
        def scalar_one_or_none(self):
            return existing

    class Db:
        async def execute(self, statement):
            statements.append(str(statement))
            return Result()

    result = await agent_kill_switch_service.assert_kill(
        Db(),
        scope=AgentKillScope.AGENT,
        reason="incident",
        asserted_by=uuid4(),
        tenant_id=tenant_id,
        agent_instance_id=agent_id,
    )
    assert result is existing
    assert len(statements) == 3
    # Ownership is validated before the scope lock; the active row is
    # locked only after the advisory lock has serialized the scope.
    assert "agent_instances" in statements[0]
    assert "pg_advisory_xact_lock" in statements[1]
    assert "FOR UPDATE" in statements[2]


@pytest.mark.asyncio
async def test_revoke_kill_enforces_tenant_ownership():
    tenant_id, other_tenant = uuid4(), uuid4()
    switch = AgentKillSwitch(
        id=uuid4(), tenant_id=tenant_id, scope=AgentKillScope.TENANT,
        active=True, reason="incident", correlation_id="corr-4",
    )

    class Result:
        def scalar_one_or_none(self):
            return switch

    class Db:
        async def execute(self, statement):
            return Result()

    with pytest.raises(ValidationAppError, match="tenant mismatch"):
        await agent_kill_switch_service.revoke_kill(
            Db(), kill_switch_id=switch.id, actor_id=uuid4(), tenant_id=other_tenant,
        )
    assert switch.active is True


@pytest.mark.asyncio
async def test_revoke_kill_is_idempotent_for_inactive_switch():
    switch = AgentKillSwitch(
        id=uuid4(), tenant_id=uuid4(), scope=AgentKillScope.AGENT,
        active=False, reason="incident", correlation_id="corr-5",
    )

    class Result:
        def scalar_one_or_none(self):
            return switch

    class Db:
        async def execute(self, statement):
            return Result()

    result = await agent_kill_switch_service.revoke_kill(
        Db(), kill_switch_id=switch.id, actor_id=uuid4(), tenant_id=switch.tenant_id,
    )
    assert result is switch
    assert switch.revoked_at is None


@pytest.mark.asyncio
async def test_revoke_kill_reports_missing_switch():
    class Result:
        def scalar_one_or_none(self):
            return None

    class Db:
        async def execute(self, statement):
            return Result()

    with pytest.raises(ConflictError, match="Kill switch not found"):
        await agent_kill_switch_service.revoke_kill(
            Db(), kill_switch_id=uuid4(), actor_id=uuid4(), tenant_id=uuid4(),
        )
