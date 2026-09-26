from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.services import workforce_sla_service as service


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class NestedTransaction:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DB:
    def __init__(self, existing=None):
        self.existing = existing
        self.flushed = False
        self.statements = []

    async def execute(self, statement):
        self.statements.append(statement)
        return Result(self.existing)

    def add(self, item):
        self.item = item

    async def flush(self):
        self.flushed = True

    def begin_nested(self):
        return NestedTransaction()


@pytest.mark.asyncio
async def test_sla_contract_rejects_unbounded_target():
    with pytest.raises(ValidationAppError, match="between"):
        await service.upsert_contract(
            DB(),
            tenant_id=uuid4(),
            actor_user_id=uuid4(),
            max_queue_age_seconds=0,
        )


@pytest.mark.asyncio
async def test_sla_contract_creates_tenant_owned_target(monkeypatch):
    audit = {}

    async def record(*args, **kwargs):
        audit.update(kwargs)

    monkeypatch.setattr(service, "record", record)
    db = DB()

    contract = await service.upsert_contract(
        db,
        tenant_id=uuid4(),
        actor_user_id=uuid4(),
        max_queue_age_seconds=300,
    )

    assert contract.max_queue_age_seconds == 300
    assert contract.enabled is True
    assert db.flushed is True
    assert audit["action"] == "workforce.sla.created"
    assert db.statements[0]._for_update_arg is not None


@pytest.mark.asyncio
async def test_sla_contract_updates_existing_target_under_row_lock(monkeypatch):
    audit = {}

    async def record(*args, **kwargs):
        audit.update(kwargs)

    monkeypatch.setattr(service, "record", record)
    existing = type(
        "Contract",
        (),
        {
            "id": uuid4(),
            "max_queue_age_seconds": 600,
            "enabled": True,
            "effective_from": None,
            "updated_by_user_id": None,
        },
    )()
    db = DB(existing=existing)

    contract = await service.upsert_contract(
        db,
        tenant_id=uuid4(),
        actor_user_id=uuid4(),
        max_queue_age_seconds=900,
        enabled=False,
    )

    assert contract is existing
    assert contract.max_queue_age_seconds == 900
    assert contract.enabled is False
    assert contract.updated_by_user_id == audit["actor_id"]
    assert audit["action"] == "workforce.sla.updated"
    assert db.statements[0]._for_update_arg is not None
