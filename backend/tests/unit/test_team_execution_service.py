from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.models.work_item import WorkItemStatus
from app.services.team_execution import TeamExecutionError, TeamExecutionService


class FakeResult:
    def __init__(self, row=None, scalar=None):
        self._row = row
        self._scalar = scalar

    def one_or_none(self):
        return self._row

    def scalar_one_or_none(self):
        return self._scalar


class FakeSession:
    def __init__(self, installation_row, agents):
        self.installation_row = installation_row
        self.agents = list(agents)
        self.added = []
        self.flush = AsyncMock()
        self.execute_calls = 0

    def add(self, item):
        self.added.append(item)
        if getattr(item, "id", None) is None:
            item.id = uuid.uuid4()

    async def execute(self, statement):
        self.execute_calls += 1
        if self.execute_calls == 1:
            return FakeResult(row=self.installation_row)
        agent = self.agents.pop(0) if self.agents else None
        return FakeResult(scalar=agent)


@pytest.mark.asyncio
async def test_execute_is_tenant_local_and_dispatches_children():
    tenant_id = uuid.uuid4()
    installation = SimpleNamespace(id=uuid.uuid4(), enabled=True)
    version = SimpleNamespace(
        id=uuid.uuid4(),
        version=2,
        member_agent_definition_ids=[str(uuid.uuid4()), str(uuid.uuid4())],
        input_schema={},
        execution_policy={"mode": "sequential"},
        allowed_tools=["search"],
    )
    team = SimpleNamespace(id=uuid.uuid4(), slug="support", description="Support team")
    agents = [
        SimpleNamespace(id=uuid.uuid4()),
        SimpleNamespace(id=uuid.uuid4()),
    ]
    db = FakeSession((installation, version, team), agents)

    with patch("app.services.team_execution.AgentExecutionAdapter") as adapter_cls:
        adapter_cls.return_value.dispatch = AsyncMock(side_effect=[
            {"run_id": str(uuid.uuid4()), "agent_instance_id": str(agents[0].id)},
            {"run_id": str(uuid.uuid4()), "agent_instance_id": str(agents[1].id)},
        ])
        result = await TeamExecutionService(db).execute(
            tenant_id=tenant_id,
            installation_id=installation.id,
            input_data={"ticket": "T-1"},
            actor_id=uuid.uuid4(),
            idempotency_key="ticket-T-1",
            correlation_id="corr-1",
        )

    assert result["status"] == WorkItemStatus.RUNNING.value
    assert result["correlation_id"] == "corr-1"
    assert len(result["members"]) == 2
    assert len(db.added) == 3
    assert db.added[0].tenant_id == tenant_id
    assert all(item.parent_work_item_id == db.added[0].id for item in db.added[1:])
    assert all(item.tenant_id == tenant_id for item in db.added)


@pytest.mark.asyncio
async def test_execute_rejects_missing_installation_without_creating_work_items():
    db = FakeSession(None, [])
    service = TeamExecutionService(db)

    with pytest.raises(TeamExecutionError, match="team installation not found"):
        await service.execute(
            tenant_id=uuid.uuid4(),
            installation_id=uuid.uuid4(),
            input_data={},
            actor_id=uuid.uuid4(),
            idempotency_key="run-1",
        )

    assert db.added == []


@pytest.mark.asyncio
async def test_execute_rejects_team_without_enabled_agent_instance():
    tenant_id = uuid.uuid4()
    installation = SimpleNamespace(id=uuid.uuid4(), enabled=True)
    version = SimpleNamespace(id=uuid.uuid4(), version=1, member_agent_definition_ids=[str(uuid.uuid4())], input_schema={}, execution_policy={}, allowed_tools=[])
    team = SimpleNamespace(id=uuid.uuid4(), slug="ops", description=None)
    db = FakeSession((installation, version, team), [])

    with pytest.raises(TeamExecutionError, match="no enabled agent instance"):
        await TeamExecutionService(db).execute(
            tenant_id=tenant_id,
            installation_id=installation.id,
            input_data={},
            actor_id=None,
            idempotency_key="run-2",
        )

    assert len(db.added) == 1
