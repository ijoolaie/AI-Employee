from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItemStatus
from app.services import agent_workforce_manager as manager
from app.services.unified_execution import ExecutionError


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def first(self):
        return None


class Db:
    def __init__(self, agent, item, active):
        self.agent = agent
        self.item = item
        self.active = active
        self.flush = AsyncMock()
        self.calls = 0

    async def execute(self, stmt):
        self.calls += 1
        return ScalarResult(self.agent if self.calls == 1 else self.item)

    async def scalar(self, stmt):
        return self.active


@pytest.fixture(autouse=True)
def allow_kill_switch_check(monkeypatch):
    monkeypatch.setattr(manager, "assert_not_killed", AsyncMock())


@pytest.mark.asyncio
async def test_assign_work_item_enforces_max_concurrency():
    tenant_id, agent_id, item_id = uuid4(), uuid4(), uuid4()
    agent = SimpleNamespace(
        id=agent_id, tenant_id=tenant_id, enabled=True,
        status=AgentInstanceStatus.ENABLED, max_concurrency=1,
    )
    item = SimpleNamespace(
        id=item_id, tenant_id=tenant_id, status=WorkItemStatus.READY,
        executor_type=None, executor_id=None,
    )
    db = Db(agent, item, active=1)

    with pytest.raises(ExecutionError, match="concurrency limit reached"):
        await manager.assign_work_item(db, tenant_id=tenant_id, work_item_id=item_id, agent_instance_id=agent_id)
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_work_item_accepts_slot_and_binds_tenant_scoped_agent():
    tenant_id, agent_id, item_id = uuid4(), uuid4(), uuid4()
    agent = SimpleNamespace(
        id=agent_id, tenant_id=tenant_id, enabled=True,
        status=AgentInstanceStatus.ENABLED, max_concurrency=2,
    )
    item = SimpleNamespace(
        id=item_id, tenant_id=tenant_id, status=WorkItemStatus.READY,
        executor_type=None, executor_id=None,
    )
    db = Db(agent, item, active=1)

    result = await manager.assign_work_item(db, tenant_id=tenant_id, work_item_id=item_id, agent_instance_id=agent_id)

    assert result is item
    assert item.executor_type is ExecutorType.AGENT
    assert item.executor_id == agent_id
    assert item.status is WorkItemStatus.ASSIGNED
    db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_assign_work_item_is_idempotent_for_same_agent():
    tenant_id, agent_id, item_id = uuid4(), uuid4(), uuid4()
    agent = SimpleNamespace(
        id=agent_id, tenant_id=tenant_id, enabled=True,
        status=AgentInstanceStatus.ENABLED, max_concurrency=1,
    )
    item = SimpleNamespace(
        id=item_id, tenant_id=tenant_id, status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT, executor_id=agent_id,
    )
    db = Db(agent, item, active=1)

    result = await manager.assign_work_item(db, tenant_id=tenant_id, work_item_id=item_id, agent_instance_id=agent_id)

    assert result is item
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_work_item_fails_closed_when_kill_switch_is_active(monkeypatch):
    tenant_id, agent_id, item_id = uuid4(), uuid4(), uuid4()
    db = Db(agent=None, item=None, active=0)

    async def deny(*args, **kwargs):
        raise ValidationAppError("Agent execution revoked by emergency kill switch")

    monkeypatch.setattr(manager, "assert_not_killed", deny)

    with pytest.raises(ValidationAppError, match="emergency kill switch"):
        await manager.assign_work_item(
            db,
            tenant_id=tenant_id,
            work_item_id=item_id,
            agent_instance_id=agent_id,
        )
    assert db.calls == 0
