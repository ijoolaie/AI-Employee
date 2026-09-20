import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.api.v1.channel_webhooks import _enqueue_whatsapp_message


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        if self.value is None:
            raise AssertionError("expected a row")
        return self.value

    def scalars(self):
        return self

    def first(self):
        return self.value


class _Db:
    def __init__(self, results):
        self.results = iter(results)
        self.added = []

    async def execute(self, _statement):
        return next(self.results)

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None

    def begin_nested(self):
        class _Savepoint:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        return _Savepoint()


@pytest.mark.asyncio
async def test_duplicate_provider_message_returns_existing_run_without_creating_run(monkeypatch):
    tenant_id = uuid.uuid4()
    channel_id = uuid.uuid4()
    conversation_id = uuid.uuid4()
    run_id = uuid.uuid4()

    channel = SimpleNamespace(
        id=channel_id,
        tenant_id=tenant_id,
        employee_id=uuid.uuid4(),
    )
    duplicate = SimpleNamespace(
        conversation_id=conversation_id,
        run_id=run_id,
    )
    conversation = SimpleNamespace(id=conversation_id)

    db = _Db([_ScalarResult(duplicate), _ScalarResult(conversation)])

    create_run = AsyncMock()
    monkeypatch.setattr("app.services.run_service.create_run", create_run)

    existing, returned_run_id, is_duplicate = await _enqueue_whatsapp_message(
        db,
        channel,
        from_phone="+989121234567",
        text="hello",
        provider_message_id="wamid-1",
    )

    assert existing.id == conversation_id
    assert returned_run_id == run_id
    assert is_duplicate is True
    create_run.assert_not_awaited()
    assert db.added == []


def test_whatsapp_message_model_exposes_channel_scoped_provider_key():
    from app.models.conversation import CustomerMessage

    assert hasattr(CustomerMessage, "channel_id")
    assert hasattr(CustomerMessage, "provider_message_id")
