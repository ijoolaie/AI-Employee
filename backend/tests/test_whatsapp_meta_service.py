import hashlib
import hmac

import pytest

from app.services.whatsapp_meta_service import (
    extract_text_messages,
    send_text_message,
    verify_webhook_challenge,
    verify_webhook_signature,
)


def test_meta_signature_requires_raw_body_and_sha256_prefix():
    body = b'{"entry":[]}'
    secret = "app-secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(body, signature, secret)
    assert not verify_webhook_signature(body, signature, "wrong-secret")
    assert not verify_webhook_signature(body + b"x", signature, secret)
    assert not verify_webhook_signature(body, "bad=" + signature[7:], secret)
    assert not verify_webhook_signature(body, None, secret)


def test_meta_webhook_challenge_is_fail_closed():
    assert verify_webhook_challenge("subscribe", "verify-me", "123", "verify-me") == "123"
    assert verify_webhook_challenge("subscribe", "wrong", "123", "verify-me") is None
    assert verify_webhook_challenge("unsubscribe", "verify-me", "123", "verify-me") is None
    assert verify_webhook_challenge("subscribe", "verify-me", None, "verify-me") is None


def test_extract_text_messages_ignores_non_text_and_empty_messages():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": {"messages": [
            {"id": "m1", "from": "15550001", "type": "text", "text": {"body": " hello "}},
            {"id": "m2", "from": "15550002", "type": "image", "image": {"id": "img"}},
            {"id": "m3", "from": "15550003", "type": "text", "text": {"body": "   "}},
        ]}}]}],
    }
    assert extract_text_messages(payload) == [{"from_phone": "15550001", "text": "hello", "message_id": "m1"}]


def test_send_text_message_fails_closed_without_provider_credentials():
    with pytest.raises(RuntimeError, match="credentials are not configured"):
        send_text_message(access_token=None, phone_number_id=None, to_phone="15550001", text="hello")
