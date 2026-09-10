"""Provider abstraction tests for the local-first AI Gateway path."""

from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest

from app.ai.providers.lm_studio_provider import LMStudioProvider
from app.ai.providers.registry import get_default_provider
from app.ai.schemas import ChatMessage, ChatRequest


def test_registry_defaults_to_lm_studio(monkeypatch):
    fake_settings = SimpleNamespace(
        ai_default_provider="lm_studio",
        lm_studio_base_url="http://127.0.0.1:1234/v1",
        lm_studio_api_key=None,
        anthropic_api_key=None,
    )
    monkeypatch.setattr("app.ai.providers.registry.get_settings", lambda: fake_settings)
    provider = get_default_provider()
    assert isinstance(provider, LMStudioProvider)
    assert provider.name == "lm_studio"
    assert provider.base_url == "http://127.0.0.1:1234/v1"


def test_lm_studio_cost_is_zero():
    provider = LMStudioProvider(base_url="http://127.0.0.1:1234/v1", api_key=None)
    assert provider.estimate_cost_usd("google/gemma-4-e4b", 1000, 500) == 0.0


@pytest.mark.asyncio
async def test_lm_studio_provider_maps_openai_compatible_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [{
                    "message": {"role": "assistant", "content": "Brief local reply."},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 12, "completion_tokens": 7},
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.ai.providers.lm_studio_provider.httpx.AsyncClient", FakeClient)
    provider = LMStudioProvider(base_url="http://127.0.0.1:1234/v1", api_key=None)
    result = await provider.chat(
        ChatRequest(messages=[ChatMessage(role="user", content="Hello")], model="google/gemma-4-e4b")
    )
    assert result.content == "Brief local reply."
    assert result.prompt_tokens == 12
    assert result.completion_tokens == 7
    assert result.stop_reason == "stop"


@pytest.mark.asyncio
async def test_gateway_records_live_latency_and_gateway_cost(monkeypatch):
    import asyncio
    import uuid

    from app.ai.gateway import AIGateway
    from app.ai.schemas import ChatResult
    from app.models.ai_provider_call import AIProviderCall
    from app.models.usage import UsageEvent

    class FakeProvider:
        name = "fake"

        async def chat(self, request):
            await asyncio.sleep(0.02)
            return ChatResult(content="ok", prompt_tokens=10, completion_tokens=5)

        def estimate_cost_usd(self, model, prompt_tokens, completion_tokens):
            return 0.123456

    class FakeDB:
        def __init__(self):
            self.items = []

        def add(self, item):
            self.items.append(item)

        async def execute(self, statement):
            class EmptyResult:
                def scalar_one_or_none(self):
                    return None

                def one_or_none(self):
                    return None

            return EmptyResult()

        async def flush(self):
            return None

        async def get(self, model, key):
            return next((item for item in self.items if getattr(item, "id", None) == key), None)

    audit_calls = []

    async def fake_audit_record(*args, **kwargs):
        audit_calls.append(kwargs)

    monkeypatch.setattr("app.ai.gateway.audit_service.record", fake_audit_record)

    db = FakeDB()
    gateway = AIGateway(provider=FakeProvider())
    result = await gateway.chat(
        db,
        ChatRequest(messages=[ChatMessage(role="user", content="hello")], model="fake-model"),
        tenant_id=uuid.uuid4(),
    )

    provider_calls = [item for item in db.items if isinstance(item, AIProviderCall)]
    usage_events = [item for item in db.items if isinstance(item, UsageEvent)]
    assert result.cost_usd == 0.123456
    assert result.latency_ms >= 15
    assert len(provider_calls) == 1
    assert provider_calls[0].cost_usd == 0.123456
    assert provider_calls[0].latency_ms >= 15
    assert len(usage_events) == 1
    assert usage_events[0].cost_usd == 0.123456
    assert audit_calls[0]["metadata"]["latency_ms"] >= 15


@pytest.mark.asyncio
async def test_run_scoped_provider_failure_fences_blind_replay(monkeypatch):
    import uuid

    from app.ai.gateway import AIGateway, AIProviderCallAmbiguous
    from app.ai.schemas import ChatResult
    from app.models.ai_provider_call import AIProviderCall

    durable_rows = {}

    class FakeDurableDB:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, model, key):
            return durable_rows.get(key)

        def add(self, item):
            durable_rows[item.id] = item

        async def commit(self):
            return None

    monkeypatch.setattr("app.ai.gateway.AsyncSessionLocal", lambda: FakeDurableDB())

    class FakeDB:
        async def execute(self, statement):
            class EmptyResult:
                def one_or_none(self):
                    return None
            return EmptyResult()

    calls = 0

    class FailingProvider:
        name = "fake"

        async def chat(self, request):
            nonlocal calls
            calls += 1
            raise TimeoutError("provider response became ambiguous")

        def estimate_cost_usd(self, model, prompt_tokens, completion_tokens):
            return 0.0

    tenant_id = uuid.uuid4()
    run_id = uuid.uuid4()
    request = ChatRequest(messages=[ChatMessage(role="user", content="hello")], model="fake-model")
    gateway = AIGateway(provider=FailingProvider())

    with pytest.raises(TimeoutError):
        await gateway.chat(
            FakeDB(), request, tenant_id=tenant_id, run_id=run_id,
            call_metadata={"tool_iteration": 0},
        )

    row = next(iter(durable_rows.values()))
    assert isinstance(row, AIProviderCall)
    assert row.status == "unknown"

    with pytest.raises(AIProviderCallAmbiguous):
        await gateway.chat(
            FakeDB(), request, tenant_id=tenant_id, run_id=run_id,
            call_metadata={"tool_iteration": 0},
        )
    assert calls == 1
