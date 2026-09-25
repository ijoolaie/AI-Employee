from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.work_item import WorkItemStatus
from app.services.team_execution import TeamExecutionError, TeamExecutionService


class _Result:
    def __init__(self, *, scalar=None, one=None, scalars=None):
        self._scalar = scalar
        self._one = one
        self._scalars = scalars or []

    def scalar_one_or_none(self):
        return self._scalar

    def one_or_none(self):
        return self._one

    def scalars(self):
        return self

    def all(self):
        return self._scalars


class _Nested:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _ReplayDb:
    def __init__(self, parent, children):
        self.results = [
            _Result(scalar=parent),
            _Result(scalars=children),
        ]
        self.added = []

    async def execute(self, _statement):
        return self.results.pop(0)


class _RaceDb:
    def __init__(self, installation, existing, children):
        self.results = [
            _Result(scalar=None),
            _Result(one=installation),
            _Result(scalar=existing),
            _Result(scalars=children),
        ]
        self.added = []

    async def execute(self, _statement):
        return self.results.pop(0)

    def begin_nested(self):
        return _Nested()

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        raise IntegrityError("duplicate", {}, Exception("duplicate"))


@pytest.mark.asyncio
async def test_team_execution_replay_returns_existing_parent_and_children():
    tenant_id = uuid4()
    installation_id = uuid4()
    parent = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        idempotency_key=f"team:{installation_id}:same-key",
        input_data={"customer_id": "c-1"},
        policy_context={
            "team_installation_id": str(installation_id),
            "team_version_id": str(uuid4()),
            "correlation_id": "corr-1",
        },
        status=WorkItemStatus.RUNNING,
    )
    child = SimpleNamespace(id=uuid4(), status=WorkItemStatus.ASSIGNED)
    db = _ReplayDb(parent, [child])

    result = await TeamExecutionService(db).execute(
        tenant_id=tenant_id,
        installation_id=installation_id,
        input_data={"customer_id": "c-1"},
        actor_id=uuid4(),
        idempotency_key="same-key",
    )

    assert result["work_item_id"] == str(parent.id)
    assert result["members"] == [
        {"work_item_id": str(child.id), "status": WorkItemStatus.ASSIGNED.value}
    ]
    assert db.added == []


@pytest.mark.asyncio
async def test_team_execution_rejects_reused_key_for_different_request():
    tenant_id = uuid4()
    installation_id = uuid4()
    parent = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        idempotency_key=f"team:{installation_id}:same-key",
        input_data={"customer_id": "c-1"},
        policy_context={"team_installation_id": str(installation_id)},
        status=WorkItemStatus.RUNNING,
    )
    db = _ReplayDb(parent, [])

    with pytest.raises(TeamExecutionError, match="different team execution"):
        await TeamExecutionService(db).execute(
            tenant_id=tenant_id,
            installation_id=installation_id,
            input_data={"customer_id": "c-2"},
            actor_id=uuid4(),
            idempotency_key="same-key",
        )


@pytest.mark.asyncio
async def test_team_execution_recovers_from_concurrent_parent_insert():
    tenant_id = uuid4()
    installation_id = uuid4()
    existing = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        idempotency_key=f"team:{installation_id}:race-key",
        input_data={"customer_id": "c-1"},
        policy_context={
            "team_installation_id": str(installation_id),
            "team_version_id": str(uuid4()),
            "correlation_id": "corr-race",
        },
        status=WorkItemStatus.RUNNING,
    )
    child = SimpleNamespace(id=uuid4(), status=WorkItemStatus.ASSIGNED)
    installation = (
        SimpleNamespace(
            id=installation_id,
            tenant_id=tenant_id,
            enabled=True,
        ),
        SimpleNamespace(
            id=uuid4(),
            version=1,
            member_agent_definition_ids=[str(uuid4())],
            input_schema={},
            execution_policy={},
            allowed_tools=[],
        ),
        SimpleNamespace(
            id=uuid4(),
            slug="team",
            description="team",
            enabled=True,
        ),
    )
    db = _RaceDb(installation, existing, [child])

    result = await TeamExecutionService(db).execute(
        tenant_id=tenant_id,
        installation_id=installation_id,
        input_data={"customer_id": "c-1"},
        actor_id=uuid4(),
        idempotency_key="race-key",
    )

    assert result["work_item_id"] == str(existing.id)
    assert result["members"][0]["work_item_id"] == str(child.id)
    assert len(db.added) == 1
