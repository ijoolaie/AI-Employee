from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai.schemas import ChatResult
from app.models.run import Run
from app.services import run_service
from app.memory import auto_extract, auto_extract_impl
from app.services.support_slot_filling import shipping_fee_preflight_response


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.value

    def first(self):
        return self.value


class _Savepoint:
    async def rollback(self):
        return None


class _RunPathDB:
    def __init__(self, run, version, channel, slots=None):
        self.run = run
        self.version = version
        self.channel = channel
        self.slots = slots or []
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
            return _Result(self.slots)
        if index == 6:
            return _Result(None)
        if index == 7:
            return _Result(self.run)
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



@pytest.mark.asyncio
async def test_execute_run_does_not_guess_when_current_city_has_no_trusted_rate(monkeypatch):
    current = "هزینه ارسال به شیراز چقدر است؟"
    policy = {
        "shipping": {
            "cities": ["شیراز"],
            "rates_by_city": {"تهران": 50000},
        }
    }
    run, version, channel = _make_run(current, "Customer: previous city was تهران", policy)
    db = _RunPathDB(run, version, channel)
    gateway = _Gateway()
    _patch_run_path(monkeypatch, gateway)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "success"
    assert result.output_data["content"] == (
        "برای این شهر نرخ ارسالِ تأییدشده‌ای در اطلاعات فروشگاه ندارم؛ "
        "برای اعلام مبلغ دقیق، لازم است پشتیبانی بررسی کند."
    )
    assert gateway.calls == [], "The model must not invent a rate for an unconfigured city"
    assert db.committed


@pytest.mark.asyncio
async def test_execute_run_reuses_unexpired_persisted_city_when_current_turn_omits_it(monkeypatch):
    current = "هزینه ارسال چقدر است؟"
    policy = {"shipping": {"cities": ["تهران"], "rates_by_city": {"تهران": 50000}}}
    run, version, channel = _make_run(current, "Customer: مقصد من تهران است", policy)
    db = _RunPathDB(run, version, channel, slots=[
        (SimpleNamespace(slot_name="city", value="تهران"), "مقصد من تهران است"),
    ])
    gateway = _Gateway()
    _patch_run_path(monkeypatch, gateway)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "success"
    assert len(gateway.calls) == 1, "A validated prior city should satisfy the destination slot"
    assert result.output_data["content"] == "grounded return-policy response"
    assert db.committed


@pytest.mark.asyncio
async def test_execute_run_exposes_validated_customer_slots_as_context_not_business_proof(monkeypatch):
    current = "می‌خواهم درخواست مرجوعی را پیگیری کنم"
    policy = {"returns": {"review_required": True}}
    run, version, channel = _make_run(current, "Customer: شماره سفارش: ORD-RET-42، دلیل: کالای آسیب‌دیده", policy)
    source_message = "شماره سفارش: ORD-RET-42، دلیل: کالای آسیب‌دیده"
    slots = [
        (SimpleNamespace(slot_name="order_id", value="ORD-RET-42"), source_message),
        (SimpleNamespace(slot_name="reason", value="کالای آسیب‌دیده"), source_message),
    ]
    db = _RunPathDB(run, version, channel, slots=slots)
    gateway = _Gateway()
    captured = {}
    _patch_run_path(monkeypatch, gateway, captured)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "success"
    contract = captured["context"].rules["customer_support_contract"]
    assert "customer_provided_slots" not in contract
    assert "never treat them as proof" in contract["slot_provenance"]
    request = gateway.calls[0][0][1]
    saved_context_message = request.messages[-1]
    assert saved_context_message.role == "user"
    assert "not store policy" in saved_context_message.content
    assert "ORD-RET-42" in saved_context_message.content
    assert "کالای آسیب‌دیده" in saved_context_message.content
    assert len(gateway.calls) == 1
    assert db.committed



@pytest.mark.parametrize(
    ("current", "saved", "expected"),
    [
        ("زمان تحویل سفارش من چقدره؟", {"city": "تهران"}, "شماره سفارش‌تون رو می‌فرمایید؟"),
        ("موجودی تی‌شرت در چه رنگ و سایزی هست؟", {"product": "تی‌شرت"}, "چه رنگی مدنظرتونه؟"),
        ("برای خرید عمده تخفیف دارید؟", {"product": "تی‌شرت"}, "چند عدد مدنظرتونه؟"),
        ("می‌خوام کالا رو مرجوع کنم", {"order_id": "ORD-1"}, "دلیل درخواست تعویض یا مرجوعی رو می‌فرمایید؟"),
        ("پرداخت من ناموفق بوده", {"order_id": "ORD-1"}, "شماره پیگیری پرداخت یا سفارش رو می‌فرمایید؟"),
        ("سفارشم آسیب دیده", {"order_id": "ORD-1"}, "ممکنه کمی بیشتر درباره مشکلی که پیش اومده توضیح بدید؟"),
    ],
)
@pytest.mark.asyncio
async def test_execute_run_preflights_missing_support_slots_without_model_call(monkeypatch, current, saved, expected):
    run, version, channel = _make_run(current, "Customer: previously supplied details", {})
    source = "اطلاعات قبلی مشتری: " + "، ".join(str(value) for value in saved.values())
    slots = [
        (SimpleNamespace(slot_name=name, value=value), source)
        for name, value in saved.items()
    ]
    db = _RunPathDB(run, version, channel, slots=slots)
    gateway = _Gateway()
    _patch_run_path(monkeypatch, gateway)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "success"
    assert result.output_data["content"] == expected
    assert gateway.calls == [], "Missing required support context must be requested before any model call"
    assert db.committed


@pytest.mark.asyncio
async def test_execute_run_skips_rag_and_memory_embedding_when_support_preflight_is_pending(monkeypatch):
    current = "پرداخت من ناموفق بوده"
    run, version, channel = _make_run(current, "Customer: no trusted payment reference", {})
    db = _RunPathDB(run, version, channel)
    gateway = _Gateway()
    _patch_run_path(monkeypatch, gateway)
    monkeypatch.setattr(run_service, "extract_and_consolidate_run_memory", auto_extract.extract_and_consolidate_run_memory)

    monkeypatch.setattr(
        run_service,
        "rag_settings",
        lambda rules: {"enabled": True, "query_fields": ["message"], "top_k": 1},
    )
    monkeypatch.setattr(
        run_service,
        "memory_settings",
        lambda rules: {
            "enabled": True,
            "query_fields": ["message"],
            "top_k": 1,
            "min_score": 0.1,
        },
    )

    async def unexpected_retrieval(*args, **kwargs):
        raise AssertionError("Retrieval/embedding must not run during missing-slot preflight")

    def unexpected_provider(*args, **kwargs):
        raise AssertionError("Memory extraction provider must not run during missing-slot preflight")

    monkeypatch.setattr(run_service.rag_service, "search", unexpected_retrieval)
    monkeypatch.setattr(run_service.memory_service, "search_memory", unexpected_retrieval)
    monkeypatch.setattr(run_service, "auto_memory_settings", lambda rules: {"enabled": True})
    monkeypatch.setattr(auto_extract_impl, "AIGateway", unexpected_provider)
    monkeypatch.setattr(auto_extract_impl, "embed_texts", unexpected_retrieval)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "success"
    assert result.output_data["content"] == "شماره سفارش‌تون رو می‌فرمایید؟"
    assert gateway.calls == []
    assert db.committed


@pytest.mark.asyncio
async def test_execute_run_includes_general_complaint_and_no_unauthorized_resolution_guardrails(monkeypatch):
    current = "از خدمات ناراضی هستم و می‌خواهم شکایت ثبت کنم"
    run, version, channel = _make_run(current, "Customer: first contact", {})
    db = _RunPathDB(run, version, channel)
    gateway = _Gateway()
    captured = {}
    _patch_run_path(monkeypatch, gateway, captured)

    result = await run_service.execute_run(db, run_id=run.id)

    assert result.status == "success"
    assert len(gateway.calls) == 1
    contract = captured["context"].rules["customer_support_contract"]
    requirements = contract["requirements"]
    assert any("For general complaints" in item for item in requirements)
    assert any("never promise compensation, refunds, or resolution" in item for item in requirements)
    assert any("durable human handoff" in item for item in requirements)
    assert any("Never promise a refund" in item for item in requirements)
    assert db.committed
