"""Phase 6 — Stripe adapter unit tests.

These exercise real cryptographic signature verification (via the actual
Stripe SDK's HMAC-SHA256 webhook scheme, not a mock) offline — no network
call to api.stripe.com is made or needed for signature verification itself,
since it's a local HMAC check against STRIPE_WEBHOOK_SECRET. This is
distinct from create_checkout_session/create_portal_session, which DO make
real Stripe API calls and are NOT exercised here — see
documents/64_PHASE_6_STRIPE_INTEGRATION_AS_BUILT_v0.6.0.md verification
boundary for what remains genuinely unverified in this build environment.
"""

import hashlib
import hmac
import json
import time

import pytest

from app.core.config import get_settings
from app.core.exceptions import ValidationAppError
from app.services import stripe_service


WEBHOOK_SECRET = "whsec_test_only_do_not_use_in_prod"


def _sign(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    ts = timestamp if timestamp is not None else int(time.time())
    signed_payload = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _event_payload(event_id: str = "evt_test1", event_type: str = "checkout.session.completed") -> bytes:
    return json.dumps(
        {
            "id": event_id,
            "object": "event",
            "type": event_type,
            "data": {
                "object": {
                    "id": "cs_test1",
                    "object": "checkout.session",
                    "client_reference_id": None,
                    "metadata": {},
                    "customer": None,
                    "subscription": None,
                }
            },
        }
    ).encode()


@pytest.fixture(autouse=True)
def _configured_stripe(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_dummy_do_not_use")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    monkeypatch.setenv("STRIPE_PRICE_MAP", json.dumps({"business": "price_business_123", "professional": "price_pro_456"}))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_stripe_enabled_true_when_keys_set():
    assert get_settings().stripe_enabled is True


def test_stripe_disabled_without_webhook_secret(monkeypatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    get_settings.cache_clear()
    assert get_settings().stripe_enabled is False
    with pytest.raises(stripe_service.StripeNotConfiguredError):
        stripe_service._client()


def test_verify_webhook_accepts_correctly_signed_payload():
    payload = _event_payload()
    header = _sign(payload, WEBHOOK_SECRET)
    event = stripe_service.verify_and_parse_webhook(payload, header)
    assert event["id"] == "evt_test1"
    assert event["type"] == "checkout.session.completed"


def test_verify_webhook_rejects_tampered_payload():
    payload = _event_payload()
    header = _sign(payload, WEBHOOK_SECRET)
    with pytest.raises(ValidationAppError):
        stripe_service.verify_and_parse_webhook(payload + b"tampered", header)


def test_verify_webhook_rejects_wrong_secret():
    payload = _event_payload()
    header = _sign(payload, "whsec_completely_different_secret")
    with pytest.raises(ValidationAppError):
        stripe_service.verify_and_parse_webhook(payload, header)


def test_verify_webhook_rejects_missing_signature_header():
    payload = _event_payload()
    with pytest.raises(ValidationAppError):
        stripe_service.verify_and_parse_webhook(payload, None)


def test_verify_webhook_rejects_stale_timestamp():
    payload = _event_payload()
    stale_timestamp = int(time.time()) - 3600
    header = _sign(payload, WEBHOOK_SECRET, timestamp=stale_timestamp)
    with pytest.raises(ValidationAppError):
        stripe_service.verify_and_parse_webhook(payload, header)


def test_plan_code_for_price_id_maps_known_price():
    assert stripe_service._plan_code_for_price_id("price_business_123") == "business"
    assert stripe_service._plan_code_for_price_id("price_pro_456") == "professional"


def test_plan_code_for_price_id_returns_none_for_unknown_price():
    assert stripe_service._plan_code_for_price_id("price_does_not_exist") is None
