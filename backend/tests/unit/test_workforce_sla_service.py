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


class DB:
    def __init__(self, existing=None):
        self.existing = existing
        self.flushed = False

    async def execute(self, _statement):
        return Result(self.existing)

    def add(self, item):
        self.item = item

    async def flush(self):
        self.flushed = True


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
