from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.refund import PaymentRefund
from app.services import refund_service, shopify_service


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
    def __init__(self, rows, *, fail_first_flush=False):
        self.rows = list(rows)
        self.fail_first_flush = fail_first_flush
        self.flushes = 0
        self.added = []
        self.executes = 0

    async def execute(self, statement):
        row = self.rows[min(self.executes, len(self.rows) - 1)] if self.rows else None
        self.executes += 1
        return _Result(row)

    def begin_nested(self):
        return _Nested()

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        self.flushes += 1
        if self.fail_first_flush and self.flushes == 1:
            raise IntegrityError("insert", {}, RuntimeError("duplicate key"))


@pytest.mark.asyncio
async def test_record_webhook_recovers_from_unique_race():
    integration = SimpleNamespace(id=uuid4(), tenant_id=uuid4())
    existing = SimpleNamespace(webhook_id="delivery-1")
    db = _RaceDb([None, existing], fail_first_flush=True)

    accepted = await shopify_service.record_webhook(
        db, integration, "delivery-1", "ORDERS_CREATE", {"id": "order-1"}
    )

    assert accepted is False
    assert len(db.added) == 1
    assert db.executes == 2


@pytest.mark.asyncio
async def test_request_refund_recovers_from_idempotency_unique_race(monkeypatch):
    tenant_id = uuid4()
    existing = PaymentRefund(
        tenant_id=tenant_id,
        operation="refund",
        provider="stripe",
        provider_payment_intent_id="pi_123",
        amount_cents=1000,
        currency="usd",
        status="pending",
        idempotency_key="refund-key-1",
    )
    db = _RaceDb([None, existing], fail_first_flush=True)

    async def assert_payment(*args, **kwargs):
        return {"currency": "usd", "status": "succeeded"}

    async def provider_call(*args, **kwargs):
        raise AssertionError("provider must not be called after another worker wins admission")

    monkeypatch.setattr(refund_service, "_assert_payment_intent_belongs_to_tenant", assert_payment)
    monkeypatch.setattr(refund_service.stripe_service, "create_refund", provider_call)

    row = await refund_service.request_refund(
        db,
        tenant_id=tenant_id,
        operation="refund",
        payment_intent_id="pi_123",
        amount_cents=1000,
        currency="USD",
        reason="requested_by_customer",
        idempotency_key="refund-key-1",
    )

    assert row is existing
    assert db.executes == 2
    assert db.flushes == 1
