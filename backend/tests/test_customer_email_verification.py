from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import customer_channel_service


def test_customer_email_normalization_is_case_insensitive_and_trimmed():
    assert customer_channel_service._normalize_customer_email("  Customer@Example.COM ") == "customer@example.com"


def test_customer_email_verification_hash_is_bound_to_challenge_and_tenant(monkeypatch):
    monkeypatch.setattr(
        customer_channel_service,
        "get_settings",
        lambda: SimpleNamespace(secret_key="test-secret-with-enough-entropy"),
    )
    tenant_id, conversation_id, challenge_id = uuid4(), uuid4(), uuid4()
    digest = customer_channel_service._verification_code_hash(
        challenge_id=challenge_id,
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        code="123456",
    )
    assert digest != "123456"
    assert len(digest) == 64
    assert digest != customer_channel_service._verification_code_hash(
        challenge_id=uuid4(), tenant_id=tenant_id,
        conversation_id=conversation_id, code="123456",
    )
    assert digest != customer_channel_service._verification_code_hash(
        challenge_id=challenge_id, tenant_id=uuid4(),
        conversation_id=conversation_id, code="123456",
    )


class _DB:
    def __init__(self):
        self.added = []

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_public_conversation_does_not_attach_unverified_crm_customer(monkeypatch):
    tenant_id, employee_id = uuid4(), uuid4()
    channel = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, channel_type="web_widget")
    employee = SimpleNamespace(id=employee_id)
    async def get_channel(db, *, public_key):
        assert public_key == "pk_test"
        return channel, employee

    async def forbidden_upsert(*args, **kwargs):
        raise AssertionError("Unverified public contact data must not create or link CRM customers")

    monkeypatch.setattr(customer_channel_service, "get_public_channel", get_channel)
    monkeypatch.setattr(customer_channel_service.customer_service, "upsert_customer", forbidden_upsert)
    db = _DB()
    conversation, token, result_employee = await customer_channel_service.create_conversation(
        db, public_key="pk_test", customer_name="Test",
        customer_email="  Customer@Example.COM ", customer_phone=None,
    )
    assert token
    assert result_employee is employee
    assert conversation.tenant_id == tenant_id
    assert conversation.customer_email == "customer@example.com"
    assert conversation.customer_id is None
    assert conversation.verified_email is None
    assert conversation.email_verified_at is None
    assert db.added == [conversation]


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _ConversationDB:
    def __init__(self, conversation):
        self.conversation = conversation
        self.calls = 0

    async def execute(self, statement):
        self.calls += 1
        return _ScalarResult(self.conversation)


@pytest.mark.asyncio
async def test_public_orders_fail_closed_before_verified_customer_identity():
    conversation = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        customer_token_hash=customer_channel_service._hash_token("valid-token"),
        email_verified_at=None,
        verified_email=None,
        customer_id=None,
    )
    db = _ConversationDB(conversation)
    result = await customer_channel_service.get_public_customer_orders(
        db, conversation_id=conversation.id, token="valid-token"
    )
    assert result["available"] is False
    assert result["orders"] == []
    assert db.calls == 1, "Unverified identity must stop before any commerce lookup"
