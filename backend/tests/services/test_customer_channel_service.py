from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import customer_channel_service


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _DB:
    def __init__(self, value):
        self.value = value
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return _Result(self.value)


@pytest.mark.asyncio
async def test_get_conversation_locks_row_for_serialized_public_chat_sends():
    conversation = SimpleNamespace(id=uuid4())
    db = _DB(conversation)

    result = await customer_channel_service._get_conversation(
        db,
        conversation_id=conversation.id,
        token="customer-token",
    )

    assert result is conversation
    assert db.statement._for_update_arg is not None


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.value


class _SendMessageDB:
    def __init__(self, *, active_runs=0, history=None):
        self.active_runs = active_runs
        self.history = history or []
        self.calls = []
        self.added = []
        self.flushed = False
        self.rolled_back = False

    async def execute(self, statement):
        self.calls.append(statement)
        if len(self.calls) == 1:
            return _ScalarResult(self.active_runs)
        return _ScalarResult(self.history)

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        self.flushed = True

    async def rollback(self):
        self.rolled_back = True


@pytest.mark.asyncio
async def test_send_message_includes_prior_turns_in_run_input(monkeypatch):
    tenant_id, employee_id, conversation_id = uuid4(), uuid4(), uuid4()
    conversation = SimpleNamespace(
        id=conversation_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
        customer_name="Test Customer",
        customer_email=None,
        customer_phone=None,
    )
    # The service query orders newest-first, then reverses the result.
    history = [
        SimpleNamespace(
            tenant_id=tenant_id, conversation_id=conversation_id,
            role="user", content="تهران",
        ),
        SimpleNamespace(
            tenant_id=tenant_id, conversation_id=conversation_id,
            role="assistant", content="ارسال برای کدوم شهره؟",
        ),
        SimpleNamespace(
            tenant_id=tenant_id, conversation_id=conversation_id,
            role="user", content="هزینه ارسال چقدره؟",
        ),
    ]
    db = _SendMessageDB(history=history)
    run = SimpleNamespace(id=uuid4())
    captured = {}

    async def fake_get_conversation(*args, **kwargs):
        assert kwargs["conversation_id"] == conversation_id
        assert kwargs["token"] == "valid-token"
        return conversation

    async def fake_create_run(db_arg, **kwargs):
        captured.update(kwargs)
        return run

    class _Task:
        @staticmethod
        def delay(*args):
            captured["dispatched"] = args

    monkeypatch.setattr(customer_channel_service, "_get_conversation", fake_get_conversation)
    monkeypatch.setattr(customer_channel_service.run_service, "create_run", fake_create_run)
    monkeypatch.setattr(
        "app.workers.run_worker.execute_run_task",
        _Task(),
        raising=False,
    )

    # Importing the worker task may be eager in this codebase; replace its delay
    # method directly to keep this unit test independent of a running queue.
    from app.workers import run_worker
    monkeypatch.setattr(run_worker.execute_run_task, "delay", _Task.delay)

    result_conversation, result_run = await customer_channel_service.send_message(
        db, conversation_id=conversation_id, token="valid-token",
        content="و هزینه برای تهران؟",
    )

    assert result_conversation is conversation
    assert result_run is run
    message_input = captured["input_data"]["message"]
    assert "Current customer message:\nو هزینه برای تهران؟" in message_input
    assert "Customer: هزینه ارسال چقدره؟" in message_input
    assert "Assistant: ارسال برای کدوم شهره؟" in message_input
    assert "Customer: تهران" in message_input
    assert message_input.index("Customer: هزینه ارسال چقدره؟") < message_input.index("Assistant: ارسال برای کدوم شهره؟") < message_input.index("Customer: تهران")
    assert "do not treat it as store policy" in message_input
    assert captured["tenant_id"] == tenant_id
    assert captured["employee_id"] == employee_id
    assert run.conversation_id == conversation_id
    assert any(getattr(item, "content", None) == "و هزینه برای تهران؟" for item in db.added)
    assert db.flushed


@pytest.mark.asyncio
async def test_send_message_blocks_new_turn_while_run_is_active(monkeypatch):
    conversation = SimpleNamespace(
        id=uuid4(), tenant_id=uuid4(), employee_id=uuid4(),
        customer_name=None, customer_email=None, customer_phone=None,
    )
    db = _SendMessageDB(active_runs=1)

    async def fake_get_conversation(*args, **kwargs):
        return conversation

    monkeypatch.setattr(customer_channel_service, "_get_conversation", fake_get_conversation)

    from app.core.exceptions import ConflictError
    with pytest.raises(ConflictError, match="wait for the current assistant response"):
        await customer_channel_service.send_message(
            db, conversation_id=conversation.id, token="valid-token",
            content="پیام دوم",
        )

    assert len(db.calls) == 1
    assert db.added == []
