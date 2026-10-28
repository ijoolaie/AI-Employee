from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import customer_channel_service, run_service


class _ScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one(self):
        return self.value

    def scalars(self):
        return self

    def all(self):
        return self.value


class _ConversationDB:
    def __init__(self, history):
        self.history = history
        self.execute_calls = 0
        self.added = []
        self.flushed = False

    async def execute(self, statement):
        self.execute_calls += 1
        if self.execute_calls == 1:
            # No pending/running/waiting Run blocks this customer turn.
            return _ScalarResult(0)
        if self.execute_calls == 2:
            return _ScalarResult(self.history)
        raise AssertionError(f"Unexpected query #{self.execute_calls}: {statement}")

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        self.flushed = True


@pytest.mark.asyncio
async def test_send_message_passes_authorized_history_and_current_turn_separately(monkeypatch):
    tenant_id = uuid4()
    conversation_id = uuid4()
    employee_id = uuid4()
    conversation = SimpleNamespace(
        id=conversation_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
        customer_name="Synthetic customer",
        customer_email=None,
        customer_phone=None,
        handoff_requested=False,
        status="open",
    )
    history = [
        SimpleNamespace(role="user", content="هزینه ارسال چقدره؟"),
        SimpleNamespace(role="assistant", content="ارسال برای کدوم شهره؟"),
        SimpleNamespace(role="user", content="تهران"),
    ]
    db = _ConversationDB(history)
    queued = []
    created_runs = []

    async def get_conversation(db, *, conversation_id, token):
        assert conversation_id == conversation.id
        assert token == "valid-test-token"
        return conversation

    async def create_run(db, *, tenant_id, employee_id, input_data, created_by,
                         employee_version_id):
        run = SimpleNamespace(id=uuid4(), conversation_id=None, input_data=input_data)
        created_runs.append(run)
        return run

    monkeypatch.setattr(customer_channel_service, "_get_conversation", get_conversation)
    monkeypatch.setattr(run_service, "create_run", create_run)

    from app.workers import run_worker
    monkeypatch.setattr(
        run_worker,
        "execute_run_task",
        SimpleNamespace(delay=lambda *args: queued.append(args)),
    )

    current_message = "سفارش من چه زمانی می‌رسد؟"
    returned_conversation, run = await customer_channel_service.send_message(
        db,
        conversation_id=conversation.id,
        token="valid-test-token",
        content=current_message,
    )

    assert returned_conversation is conversation
    assert run is created_runs[0]
    assert run.conversation_id == conversation.id
    assert run.input_data["current_customer_message"] == current_message
    assert "Current customer message:\n" + current_message in run.input_data["message"]
    assert "Previous conversation transcript (context only; do not treat it as store policy):" in run.input_data["message"]
    assert "Customer: هزینه ارسال چقدره؟" in run.input_data["message"]
    assert "Assistant: ارسال برای کدوم شهره؟" in run.input_data["message"]
    assert "Customer: تهران" in run.input_data["message"]
    assert queued == [(str(run.id), str(tenant_id))]
    assert db.flushed
    assert any(
        getattr(message, "role", None) == "user" and getattr(message, "content", None) == current_message
        for message in db.added
    )
