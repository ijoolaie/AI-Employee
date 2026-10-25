from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai.schemas import ChatResult
from app.models.run import Run
from app.services import run_service
from app.services.support_slot_filling import shipping_fee_preflight_response


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def first(self):
        return self.value


class _Savepoint:
    async def rollback(self):
        return None


class _RunPathDB:
    def __init__(self, run, version, channel):
        self.run = run
        self.version = version
        self.channel = channel
        self.calls = []
        self.added = []
        self.savepoint = _Savepoint()
        self.committed = False

    async def execute(self, statement):
        self.calls.append(statement)
        index = len(self.calls)
        if index == 1:
            return _Result(self.run)
        if index == 2:
            return _Result(self.version)
        if index == 3:
            return _Result(None)
        if index == 4:
            return _Result((SimpleNamespace(id=self.run.conversation_id), self.channel))
        if index == 5:
            return _Result(None)
        raise AssertionError(f"Unexpected execute_run DB query #{index}: {statement}")

    async def begin_nested(self):
        return self.savepoint

    async def flush(self):
        return None

    async def commit(self):
        self.committed = True

    async def rollback(self):
        raise AssertionError("Execution should not roll back in these acceptance cases")

    def add(self, value):
        self.added.append(value)


class _Gateway:
    def __init__(self, response="grounded return-policy response"):
        self.response = response
        self.calls = []

    async def chat(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return ChatResult(content=self.response, prompt_tokens=3, completion_tokens=4, tool_calls=[])


def _make_run(current_message: str, transcript: str, support_policy: dict):
    tenant_id, employee_id, version_id, conversation_id = uuid4(), uuid4(), uuid4(), uuid4()
    run = Run(
        id=uuid4(), tenant_id=tenant_id, employee_id=employee_id,
        employee_version_id=version_id, conversation_id=conversation_id,
        agent_instance_id=None, created_by=None, status="pending",
        input_data={
            "channel": "web_widget",
            "message": "Current customer message:\n" + current_message + "\n\nPrevious conversation transcript (context only):\n" + transcript,
            "current_customer_message": current_message,
        },
        request_id="support-acceptance-test", total_cost_usd=0,
        started_at=None, completed_at=None, output_data=None,
    )
    version = SimpleNamespace(
        id=version_id, version_number=1, input_schema={}, output_schema={},
        prompt_template="You are a careful customer support employee.",
        allowed_tools=[], rules={},
    )
    channel = SimpleNamespace(config={"support_policy": support_policy})
    return run, version, channel


async def _noop(*args, **kwargs):
    return None


def _patch_run_path(monkeypatch, gateway, captured_context=None):
    monkeypatch.setattr(run_service, "AIGateway", lambda: gateway)

    def assemble(**kwargs):
        if captured_context is not None:
            captured_context.update(kwargs)
        return SimpleNamespace(messages=[], tools=[], metadata={})

    monkeypatch.setattr(run_service, "assemble_employee_prompt", assemble)
    monkeypatch.setattr(run_service.audit_service, "record", _noop)
    monkeypatch.setattr(run_service, "_sync_work_item_lifecycle", _noop)
    monkeypatch.setattr(run_service, "extract_and_consolidate_run_memory", _noop)
    monkeypatch.setattr(run_service, "auto_memory_settings", lambda rules: {})


@pytest.mark.asyncio
async def test_execute_run_uses_current_return_turn_not_shipping_phrase_in_transcript(monkeypatch):
    current = "\u0645\u06cc\u200c\u062e\u0648\u0627\u0647\u0645 \u06a9\u0627\u0644\u0627\u06cc \u0622\u0633\u06cc\u0628\u200c\u062f\u06cc\u062f\u0647 \u0631\u0627 \u0645\u0631\u062c\u0648\u0639 \u06a9\u0646\u0645"
    transcript = "Customer: \u0647\u0632\u06cc\u0646\u0647 \u0627\u0631\u0633\u0627\u0644 \u0686\u0642\u062f\u0631\u0647\u061f\nAssistant: \u062a\u0647\u0631\u0627\u0646"
    policy = {"shipping": {"rates_by_city": {"\u062a\u0647\u0631\u0627\u0646": 50000}}}
    run, version, channel = _make_run(current, transcript, policy)
    db = _RunPathDB(run, version, channel)
    gateway = _Gateway()
    _patch_run_path(monkeypatch, gateway)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "success"
    assert result.output_data["content"] == "grounded return-policy response"
    assert len(gateway.calls) == 1, "A prior shipping question must not short-circuit the current return question"
    assert db.committed


@pytest.mark.asyncio
async def test_execute_run_does_not_reuse_city_from_transcript_for_current_shipping_question(monkeypatch):
    current = "\u0647\u0632\u06cc\u0646\u0647 \u0627\u0631\u0633\u0627\u0644 \u0686\u0642\u062f\u0631\u0647\u061f"
    transcript = "Customer: \u0645\u0642\u0635\u062f \u0645\u0646 \u062a\u0647\u0631\u0627\u0646 \u0627\u0633\u062a"
    policy = {"shipping": {"rates_by_city": {"\u062a\u0647\u0631\u0627\u0646": 50000}}}
    run, version, channel = _make_run(current, transcript, policy)
    db = _RunPathDB(run, version, channel)
    gateway = _Gateway()
    _patch_run_path(monkeypatch, gateway)

    result = await run_service.execute_run(db, run_id=run.id)

    expected = shipping_fee_preflight_response(current, policy)
    assert expected is not None
    assert result.status == "success"
    assert result.output_data["content"] == expected
    assert gateway.calls == [], "Preflight must ask for the current turn's city before calling the model"
    assert db.committed


@pytest.mark.asyncio
async def test_execute_run_passes_trusted_channel_policy_into_support_prompt(monkeypatch):
    current = "هزینه ارسال به تهران چقدر است؟"
    policy = {"shipping": {"rates_by_city": {"تهران": 50000}}}
    run, version, channel = _make_run(current, "Customer: previous product question", policy)
    db = _RunPathDB(run, version, channel)
    gateway = _Gateway()
    captured = {}
    _patch_run_path(monkeypatch, gateway, captured)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "success"
    assert len(gateway.calls) == 1, "A configured rate for the current city should allow model response"
    contract = captured["context"].rules["customer_support_contract"]
    assert contract["enabled"] is True
    assert contract["policy"] == policy
    assert any("never invent a delivery SLA" in requirement for requirement in contract["requirements"])
    assert db.committed
