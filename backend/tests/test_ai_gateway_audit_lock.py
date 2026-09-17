import uuid
from contextlib import asynccontextmanager

import pytest

from app.ai.gateway import AIGateway
from app.ai.schemas import ChatMessage, ChatRequest, ChatResult
from app.models.ai_provider_call import AIProviderCall


@pytest.mark.asyncio
async def test_run_scoped_ai_audit_is_written_on_caller_transaction(monkeypatch):
    class FakeDurableDB:
        def __init__(self):
            self.items = {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, model, key):
            return self.items.get(key)

        def add(self, item):
            self.items[item.id] = item

        async def flush(self):
            return None

        async def commit(self):
            return None

    class FakeDB:
        def __init__(self):
            self.items = []

        async def execute(self, statement):
            class EmptyResult:
                def one_or_none(self):
                    return None

            return EmptyResult()

        async def get(self, model, key):
            return next((item for item in self.items if getattr(item, "id", None) == key), None)

        async def flush(self):
            return None

        def add(self, item):
            self.items.append(item)

    class FakeProvider:
        name = "fake"

        async def chat(self, request):
            return ChatResult(content="ok", prompt_tokens=10, completion_tokens=5)

        def estimate_cost_usd(self, model, prompt_tokens, completion_tokens):
            return 0.0

    durable_db = FakeDurableDB()
    main_db = FakeDB()
    audit_calls = []

    async def fake_usage_event(*args, **kwargs):
        return None

    async def fake_audit_record(db, **kwargs):
        audit_calls.append((db, kwargs))

    monkeypatch.setattr("app.ai.gateway.AsyncSessionLocal", lambda: durable_db)
    monkeypatch.setattr("app.ai.gateway.usage_service.record_event", fake_usage_event)
    monkeypatch.setattr("app.ai.gateway.audit_service.record", fake_audit_record)

    tenant_id = uuid.uuid4()
    run_id = uuid.uuid4()
    gateway = AIGateway(provider=FakeProvider())

    result = await gateway.chat(
        main_db,
        ChatRequest(
            messages=[ChatMessage(role="user", content="hello")],
            model="fake-model",
        ),
        tenant_id=tenant_id,
        run_id=run_id,
        call_metadata={"tool_iteration": 1},
    )

    assert result.content == "ok"
    assert len(audit_calls) == 1
    audit_db, metadata = audit_calls[0]
    assert audit_db is main_db
    assert metadata["action"] == "ai.provider_call"
    assert metadata["resource_id"] == run_id
    assert len(durable_db.items) == 1
    assert isinstance(next(iter(durable_db.items.values())), AIProviderCall)
