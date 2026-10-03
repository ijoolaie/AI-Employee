from decimal import Decimal

import pytest

from app.core.config import get_settings
from app.services import zarinpal_service


def test_zarinpal_rial_amount_conversion():
    assert zarinpal_service._rial_amount(Decimal("100000"), "IRR") == 100000
    assert zarinpal_service._rial_amount(Decimal("10000"), "IRT") == 100000


def test_zarinpal_rejects_non_iranian_currency():
    with pytest.raises(Exception, match="supports IRR/IRT only"):
        zarinpal_service._rial_amount(Decimal("10"), "USD")


def test_zarinpal_callback_url_binds_deal(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "zarinpal_callback_url", "https://example.test/api/v1/webhooks/billing/zarinpal")
    assert zarinpal_service._callback_url("00000000-0000-0000-0000-000000000123").endswith("deal_id=00000000-0000-0000-0000-000000000123")


@pytest.mark.asyncio
async def test_zarinpal_payment_request_requires_merchant(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "zarinpal_merchant_id", None)
    with pytest.raises(Exception, match="requires ZARINPAL_MERCHANT_ID"):
        await zarinpal_service.create_payment_request(
            tenant_id="00000000-0000-0000-0000-000000000001",
            deal_id="00000000-0000-0000-0000-000000000002",
            amount=Decimal("100000"),
            currency="IRR",
            customer_email=None,
            idempotency_key="zp-test-1",
        )


@pytest.mark.asyncio
async def test_zarinpal_payment_request_parses_success(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "zarinpal_merchant_id", "merchant-test")
    monkeypatch.setattr(settings, "zarinpal_sandbox", True)

    class FakeResponse:
        status_code = 200
        def json(self):
            return {"data": {"code": 100, "authority": "A-TEST-123"}, "errors": []}

    class FakeClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return None
        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(zarinpal_service.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    result = await zarinpal_service.create_payment_request(
        tenant_id="00000000-0000-0000-0000-000000000001",
        deal_id="00000000-0000-0000-0000-000000000002",
        amount=Decimal("100000"),
        currency="IRR",
        customer_email="customer@example.test",
        idempotency_key="zp-test-2",
    )
    assert result.provider == "zarinpal"
    assert result.provider_execution == "accepted"
    assert result.executed is True
    assert result.provider_payment_id == "A-TEST-123"
    assert result.checkout_url.endswith("/A-TEST-123")
