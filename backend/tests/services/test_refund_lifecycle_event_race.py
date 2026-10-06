from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.services import refund_service


class _Nested:
    def __init__(self, db):
        self.db = db

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None and self.db.added:
            self.db.added.pop()
        return False


class _Result:
    def __init__(self, row):
        self.row = row

    def scalar_one_or_none(self):
        return self.row


class _RaceDb:
    def __init__(self, winner, constraint_name="uq_billing_event_provider_id"):
        self.winner = winner
        self.constraint_name = constraint_name
        self.executes = 0
        self.flushes = 0
        self.added = []

    async def execute(self, statement):
        self.executes += 1
        return _Result(None if self.executes == 1 else self.winner)

    def begin_nested(self):
        return _Nested(self)

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        self.flushes += 1
        if self.flushes == 1:
            orig = SimpleNamespace(
                diag=SimpleNamespace(constraint_name=self.constraint_name)
            )
            raise IntegrityError("INSERT", {}, orig)


def _refund():
    return SimpleNamespace(
        tenant_id=uuid4(),
        id=uuid4(),
        idempotency_key="refund-42",
        operation="refund",
        provider_payment_intent_id="pi_42",
        provider_refund_id="re_42",
        amount_cents=100,
        currency="usd",
        reason="requested_by_customer",
        failure_reason=None,
    )


@pytest.mark.asyncio
async def test_record_lifecycle_event_recovers_from_expected_unique_race():
    refund = _refund()
    winner = SimpleNamespace(status="processed", payload={})
    db = _RaceDb(winner)

    await refund_service._record_lifecycle_event(db, row=refund, status="processed")

    assert db.added == []
    assert winner.status == "processed"
    assert winner.payload["refund_id"] == str(refund.id)
    assert db.executes == 2
    assert db.flushes == 2


@pytest.mark.asyncio
async def test_record_lifecycle_event_reraises_unrelated_integrity_error():
    refund = _refund()
    winner = SimpleNamespace(status="processed", payload={})
    db = _RaceDb(winner, constraint_name="some_unrelated_constraint")

    with pytest.raises(IntegrityError):
        await refund_service._record_lifecycle_event(db, row=refund, status="processed")

    assert db.executes == 1
    assert db.flushes == 1
