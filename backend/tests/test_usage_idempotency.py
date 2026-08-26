from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.usage_service import record_event


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeDB:
    def __init__(self, existing=None):
        self.existing = existing
        self.added = []

    async def execute(self, _statement):
        return FakeResult(self.existing)

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_usage_event_is_idempotent_per_tenant_and_event_key():
    tenant_id = uuid4()
    existing = SimpleNamespace(event_key="run:123", tenant_id=tenant_id)
    db = FakeDB(existing=existing)

    result = await record_event(
        db,
        tenant_id=tenant_id,
        event_key="run:123",
        category="run",
        source_type="run",
        source_id="123",
    )

    assert result is existing
    assert db.added == []


@pytest.mark.asyncio
async def test_usage_event_is_created_when_key_is_new():
    tenant_id = uuid4()
    db = FakeDB()

    result = await record_event(
        db,
        tenant_id=tenant_id,
        event_key="ai:request-1",
        category="ai_call",
        prompt_tokens=10,
        completion_tokens=20,
        cost_usd=0.01,
        source_type="ai_provider_call",
        source_id="call-1",
    )

    assert result.tenant_id == tenant_id
    assert result.event_key == "ai:request-1"
    assert result.prompt_tokens == 10
    assert result.completion_tokens == 20
    assert db.added == [result]
