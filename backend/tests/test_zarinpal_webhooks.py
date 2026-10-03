from types import SimpleNamespace
from urllib.parse import urlencode
from decimal import Decimal

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.v1 import zarinpal_webhooks
from app.core.exceptions import ConflictError


def _request(**params):
    query = urlencode(params)
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/webhooks/billing/zarinpal",
        "query_string": query.encode(),
        "headers": [],
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("testclient", 1234),
        "root_path": "",
    }
    return Request(scope)


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _Db:
    def __init__(self, deal):
        self.deal = deal
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, _statement):
        return _Result(self.deal)

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(
        zarinpal_webhooks,
        "get_settings",
        lambda: SimpleNamespace(zarinpal_merchant_id="test-merchant"),
    )


@pytest.mark.asyncio
async def test_zarinpal_callback_verifies_and_reconciles(configured, monkeypatch):
    import uuid

    deal_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    authority = "A00000000000000000000000000000test"
    deal = SimpleNamespace(
        id=deal_id,
        tenant_id=tenant_id,
        amount=Decimal("100000"),
        currency="IRR",
        metadata_={
            "payment_provider": "zarinpal",
            "payment_provider_authority": authority,
        },
    )
    db = _Db(deal)
    verified = {}
    reconciled = {}

    async def fake_verify(*, authority, amount, currency):
        verified.update(authority=authority, amount=amount, currency=currency)
        return {"code": 100, "ref_id": 513655101}

    async def fake_reconcile(db, *, provider, provider_event_id, data):
        reconciled.update(
            provider=provider,
            provider_event_id=provider_event_id,
            data=data,
        )
        return tenant_id, "order-1"

    monkeypatch.setattr(zarinpal_webhooks.zarinpal_service, "verify_payment", fake_verify)
    monkeypatch.setattr(
        zarinpal_webhooks.stripe_service,
        "apply_verified_sales_payment",
        fake_reconcile,
    )

    result = await zarinpal_webhooks.receive_zarinpal_callback(
        _request(deal_id=str(deal_id), Authority=authority, Status="OK"),
        db,
    )

    assert result["success"] is True
    assert result["status"] == "paid"
    assert result["provider"] == "zarinpal"
    assert result["reference_id"] == "513655101"
    assert verified == {
        "authority": authority,
        "amount": 100000,
        "currency": "IRR",
    }
    assert reconciled["provider"] == "zarinpal"
    assert reconciled["provider_event_id"] == "513655101"
    assert reconciled["data"]["metadata"] == {
        "tenant_id": str(tenant_id),
        "sales_deal_id": str(deal_id),
    }
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_zarinpal_callback_rejects_authority_mismatch(configured):
    import uuid

    deal_id = uuid.uuid4()
    deal = SimpleNamespace(
        id=deal_id,
        tenant_id=uuid.uuid4(),
        amount=Decimal("100000"),
        currency="IRR",
        metadata_={
            "payment_provider": "zarinpal",
            "payment_provider_authority": "expected-authority",
        },
    )
    db = _Db(deal)

    with pytest.raises(HTTPException) as exc:
        await zarinpal_webhooks.receive_zarinpal_callback(
            _request(
                deal_id=str(deal_id),
                Authority="different-authority",
                Status="OK",
            ),
            db,
        )

    assert exc.value.status_code == 409
    assert "authority does not match" in str(exc.value.detail)
    assert db.commits == 0
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_zarinpal_callback_converts_reconciliation_amount_conflict_to_409(
    configured, monkeypatch
):
    import uuid

    deal_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    authority = "A00000000000000000000000000000test"
    deal = SimpleNamespace(
        id=deal_id,
        tenant_id=tenant_id,
        amount=Decimal("100000"),
        currency="IRR",
        metadata_={
            "payment_provider": "zarinpal",
            "payment_provider_authority": authority,
        },
    )
    db = _Db(deal)

    async def fake_verify(*, authority, amount, currency):
        return {"code": 100, "ref_id": 513655102}

    async def fake_reconcile(*args, **kwargs):
        raise ConflictError("Sales payment amount/currency does not match the governed deal commitment")

    monkeypatch.setattr(zarinpal_webhooks.zarinpal_service, "verify_payment", fake_verify)
    monkeypatch.setattr(
        zarinpal_webhooks.stripe_service,
        "apply_verified_sales_payment",
        fake_reconcile,
    )

    with pytest.raises(HTTPException) as exc:
        await zarinpal_webhooks.receive_zarinpal_callback(
            _request(deal_id=str(deal_id), Authority=authority, Status="OK"),
            db,
        )

    assert exc.value.status_code == 409
    assert "amount/currency" in str(exc.value.detail)
    assert db.commits == 0
    assert db.rollbacks == 1


@pytest.mark.asyncio
async def test_zarinpal_callback_non_ok_status_does_not_reconcile(configured, monkeypatch):
    import uuid

    deal_id = uuid.uuid4()
    authority = "A00000000000000000000000000000test"
    deal = SimpleNamespace(
        id=deal_id,
        tenant_id=uuid.uuid4(),
        amount=Decimal("100000"),
        currency="IRR",
        metadata_={
            "payment_provider": "zarinpal",
            "payment_provider_authority": authority,
        },
    )
    db = _Db(deal)

    async def fail_verify(**kwargs):
        raise AssertionError("cancelled callback must not verify payment")

    monkeypatch.setattr(zarinpal_webhooks.zarinpal_service, "verify_payment", fail_verify)

    result = await zarinpal_webhooks.receive_zarinpal_callback(
        _request(deal_id=str(deal_id), Authority=authority, Status="NOK"),
        db,
    )

    assert result == {
        "success": False,
        "status": "cancelled",
        "deal_id": str(deal_id),
    }
    assert db.commits == 0
    assert db.rollbacks == 0

@pytest.mark.asyncio
async def test_zarinpal_callback_replay_reaches_idempotent_reconciliation_boundary(
    configured, monkeypatch
):
    import uuid

    deal_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    authority = "A00000000000000000000000000000replay"
    deal = SimpleNamespace(
        id=deal_id,
        tenant_id=tenant_id,
        amount=Decimal("100000"),
        currency="IRR",
        metadata_={
            "payment_provider": "zarinpal",
            "payment_provider_authority": authority,
        },
    )
    db = _Db(deal)
    reconcile_calls = []

    async def fake_verify(*, authority, amount, currency):
        return {"code": 100, "ref_id": 513655103}

    async def fake_reconcile(db, *, provider, provider_event_id, data):
        reconcile_calls.append(
            (provider, provider_event_id, data["metadata"]["sales_deal_id"])
        )
        return tenant_id, "order-1"

    monkeypatch.setattr(zarinpal_webhooks.zarinpal_service, "verify_payment", fake_verify)
    monkeypatch.setattr(
        zarinpal_webhooks.stripe_service,
        "apply_verified_sales_payment",
        fake_reconcile,
    )

    first = await zarinpal_webhooks.receive_zarinpal_callback(
        _request(deal_id=str(deal_id), Authority=authority, Status="OK"),
        db,
    )
    second = await zarinpal_webhooks.receive_zarinpal_callback(
        _request(deal_id=str(deal_id), Authority=authority, Status="OK"),
        db,
    )

    assert first == second == {
        "success": True,
        "status": "paid",
        "provider": "zarinpal",
        "deal_id": str(deal_id),
        "tenant_id": str(tenant_id),
        "order_id": "order-1",
        "reference_id": "513655103",
    }
    assert reconcile_calls == [
        ("zarinpal", "513655103", str(deal_id)),
        ("zarinpal", "513655103", str(deal_id)),
    ]
    assert db.commits == 2
    assert db.rollbacks == 0

