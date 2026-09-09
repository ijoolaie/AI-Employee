from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.core.exceptions import ValidationAppError
from app.models.agent_definition import AgentDefinition
from app.models.agent_instance import AgentInstance, AgentInstanceStatus
from app.models.tenant import Tenant
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
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


@pytest.mark.asyncio
async def test_concurrent_agent_assignments_are_serialized_by_agent_row_lock():
    """Two real PostgreSQL transactions cannot both consume one Agent slot."""
    suffix = uuid4().hex
    tenant_id = uuid4()
    definition_id = uuid4()
    agent_id = uuid4()
    item_ids = (uuid4(), uuid4())

    async with AsyncSessionLocal() as db:
        tenant = Tenant(
            id=tenant_id,
            name=f"Workforce concurrency {suffix}",
            slug=f"workforce-concurrency-{suffix}",
            status="active",
        )
        definition = AgentDefinition(
            id=definition_id,
            tenant_id=tenant_id,
            slug=f"workforce-concurrency-{suffix}",
            name="Workforce concurrency test definition",
            capabilities=[],
            allowed_tools=[],
            model_policy={},
            input_schema={},
            output_schema={},
            policy_requirements={},
            enabled=True,
        )
        agent = AgentInstance(
            id=agent_id,
            tenant_id=tenant_id,
            agent_definition_id=definition_id,
            name="Workforce concurrency test agent",
            configuration={},
            permission_policy={},
            approval_policy={},
            max_concurrency=1,
            budget_policy={},
            enabled=True,
            status=AgentInstanceStatus.ENABLED,
        )
        items = [
            WorkItem(
                id=item_id,
                tenant_id=tenant_id,
                title=f"Concurrent assignment {index}",
                status=WorkItemStatus.READY,
                executor_type=None,
                executor_id=None,
                input_data={},
                policy_context={},
                idempotency_key=f"workforce-concurrency-{suffix}-{index}",
            )
            for index, item_id in enumerate(item_ids)
        ]
        db.add(tenant)
        await db.flush()
        db.add_all([definition, agent, *items])
        await db.commit()

    async def assign(item_id):
        async with AsyncSessionLocal() as db:
            try:
                item = await manager.assign_work_item(
                    db,
                    tenant_id=tenant_id,
                    work_item_id=item_id,
                    agent_instance_id=agent_id,
                )
                await db.commit()
                return item.status
            except Exception as exc:
                await db.rollback()
                return exc

    results = await asyncio.gather(*(assign(item_id) for item_id in item_ids))

    assert sum(result is WorkItemStatus.ASSIGNED for result in results) == 1
    failures = [result for result in results if isinstance(result, ExecutionError)]
    assert len(failures) == 1
    assert "concurrency limit reached" in str(failures[0])

    async with AsyncSessionLocal() as db:
        agent_row = await db.get(AgentInstance, agent_id)
        assigned_count = await db.scalar(
            select(func.count(WorkItem.id)).where(
                WorkItem.tenant_id == tenant_id,
                WorkItem.executor_type == ExecutorType.AGENT,
                WorkItem.executor_id == agent_id,
                WorkItem.status.in_(manager.ACTIVE_WORK_ITEM_STATUSES),
            )
        )
        assert agent_row is not None
        assert assigned_count == 1

        for item_id in item_ids:
            item = await db.get(WorkItem, item_id)
            assert item is not None
            assert item.status in {WorkItemStatus.READY, WorkItemStatus.ASSIGNED}
            await db.delete(item)
        await db.flush()

        await db.delete(agent_row)
        await db.flush()

        definition_row = await db.get(AgentDefinition, definition_id)
        assert definition_row is not None
        await db.delete(definition_row)
        await db.flush()

        tenant_row = await db.get(Tenant, tenant_id)
        assert tenant_row is not None
        await db.delete(tenant_row)
        await db.commit()
