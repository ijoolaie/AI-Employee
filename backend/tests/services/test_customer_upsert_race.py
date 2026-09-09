from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.services import customer_service


class _Nested:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _Result:
    def __init__(self, row):
        self.row = row

    def scalar_one_or_none(self):
        return self.row


class _RaceDb:
    def __init__(self, winner):
        self.winner = winner
        self.executes = 0
        self.flushes = 0
        self.added = []

    async def execute(self, statement):
        self.executes += 1
        return _Result(None if self.executes == 1 else self.winner)

    def begin_nested(self):
        return _Nested()

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        self.flushes += 1
        if self.flushes == 1:
            raise IntegrityError("INSERT", {}, Exception("duplicate key"))

    async def refresh(self, row):
        return None


@pytest.mark.asyncio
async def test_upsert_customer_recovers_from_unique_race():
    tenant_id = uuid4()
    winner = SimpleNamespace(
        tenant_id=tenant_id,
        external_key="shopify:customer:42",
        name="Existing",
        email="existing@example.com",
        phone=None,
        last_channel="shopify",
    )
    db = _RaceDb(winner)

    customer = await customer_service.upsert_customer(
        db,
        tenant_id=tenant_id,
        external_key="shopify:customer:42",
        name="Updated",
    )

    assert customer is winner
    assert customer.name == "Updated"
    assert len(db.added) == 1
    assert db.executes == 2
    assert db.flushes == 2
