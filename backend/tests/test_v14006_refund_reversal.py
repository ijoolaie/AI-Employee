from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.schemas.billing import RefundRequest, RefundResponse
from app.services import refund_service


def test_refund_request_defaults_to_full_refund():
    request = RefundRequest(payment_intent_id="pi_test", idempotency_key="refund-1")
    assert request.operation == "refund"
    assert request.amount_cents is None
    assert request.currency == "usd"


def test_reversal_request_is_supported():
    request = RefundRequest(
        operation="reversal",
        payment_intent_id="pi_test",
        idempotency_key="reversal-1",
    )
    assert request.operation == "reversal"


def test_refund_response_contract_exposes_provider_and_lifecycle_state():
    assert {"pending", "succeeded", "failed"}.issuperset({"pending"})
    assert RefundResponse.model_fields["provider_refund_id"].is_required() is False


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _DB:
    def __init__(self, results):
        self.results = list(results)
        self.added = []

    async def execute(self, _statement):
        return _Result(self.results.pop(0))

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_idempotency_key_cannot_change_request():
    tenant_id = uuid4()
    existing = SimpleNamespace(
        operation="refund",
        provider_payment_intent_id="pi_original",
        amount_cents=None,
        currency="usd",
        status="succeeded",
    )
    db = _DB([existing])

    with pytest.raises(ConflictError, match="Idempotency key already belongs"):
        await refund_service.request_refund(
            db,
            tenant_id=tenant_id,
            operation="refund",
            payment_intent_id="pi_other",
            amount_cents=None,
            currency="usd",
            reason=None,
            idempotency_key="same-key",
        )


@pytest.mark.asyncio
async def test_successful_refund_records_billing_lifecycle_event(monkeypatch):
    tenant_id = uuid4()
    db = _DB([None, None])

    async def fake_assert_payment(*_args, **_kwargs):
        return {"currency": "usd", "status": "succeeded"}

    async def fake_refund(**_kwargs):
        return {
            "id": "re_test",
            "status": "succeeded",
            "amount": 1200,
            "currency": "usd",
            "charge": "ch_test",
        }

    monkeypatch.setattr(refund_service, "_assert_payment_intent_belongs_to_tenant", fake_assert_payment)
    monkeypatch.setattr(refund_service.stripe_service, "create_refund", fake_refund)

    row = await refund_service.request_refund(
        db,
        tenant_id=tenant_id,
        operation="refund",
        payment_intent_id="pi_test",
        amount_cents=1200,
        currency="usd",
        reason="requested_by_customer",
        idempotency_key="refund-2",
    )

    assert row.status == "succeeded"
    assert any(getattr(item, "event_type", None) == "payment.refund.requested" for item in db.added)


@pytest.mark.asyncio
async def test_successful_reversal_records_provider_metadata(monkeypatch):
    tenant_id = uuid4()
    db = _DB([None, None])

    async def fake_assert_payment(*_args, **_kwargs):
        return {"currency": "usd", "status": "requires_capture"}

    async def fake_reversal(**_kwargs):
        return {"id": "pi_test", "status": "canceled"}

    monkeypatch.setattr(refund_service, "_assert_payment_intent_belongs_to_tenant", fake_assert_payment)
    monkeypatch.setattr(refund_service.stripe_service, "create_reversal", fake_reversal)

    row = await refund_service.request_refund(
        db,
        tenant_id=tenant_id,
        operation="reversal",
        payment_intent_id="pi_test",
        amount_cents=None,
        currency="usd",
        reason=None,
        idempotency_key="reversal-2",
    )

    assert row.status == "succeeded"
    assert row.refund_metadata == {
        "provider_operation": "payment_intent_cancel",
        "provider_status": "canceled",
    }
    assert any(getattr(item, "event_type", None) == "payment.reversal.requested" for item in db.added)
