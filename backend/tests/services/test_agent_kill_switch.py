from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_kill_switch import AgentKillScope, AgentKillSwitch
from app.services import agent_kill_switch_service


@pytest.mark.asyncio
async def test_active_agent_kill_switch_blocks_execution(monkeypatch):
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
async def test_kill_switch_scope_precedence_is_fail_closed(monkeypatch):
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
