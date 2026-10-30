from __future__ import annotations

from uuid import uuid4

from app.services.customer_channel_service import (
    _normalize_customer_email,
    _verification_code_hash,
)


def test_customer_email_normalization_is_case_insensitive_and_trimmed():
    assert _normalize_customer_email("  Customer@Example.COM ") == "customer@example.com"


def test_customer_email_verification_hash_is_bound_to_challenge_and_tenant(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(
        "app.services.customer_channel_service.get_settings",
        lambda: type("Settings", (), {"secret_key": "test-secret-with-enough-entropy"})(),
    )
    tenant_id, conversation_id, challenge_id = uuid4(), uuid4(), uuid4()
    digest = _verification_code_hash(
        challenge_id=challenge_id,
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        code="123456",
    )
    assert digest != "123456"
    assert len(digest) == 64
    assert digest != _verification_code_hash(
        challenge_id=uuid4(),
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        code="123456",
    )
    assert digest != _verification_code_hash(
        challenge_id=challenge_id,
        tenant_id=uuid4(),
        conversation_id=conversation_id,
        code="123456",
    )
