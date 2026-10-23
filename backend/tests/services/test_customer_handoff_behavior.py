"""Regression tests for customer messages received during human handoff."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import customer_channel_service


class _HandoffMessageDB:
    def __init__(self):
        self.added = []
        self.executed = 0
        self.flushed = False

    async def execute(self, statement):
        self.executed += 1
        raise AssertionError("AI run lookup must not happen during human handoff")

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        self.flushed = True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "handoff_requested"),
    [("human", True), ("human", False), ("open", True)],
)
async def test_customer_message_during_handoff_is_saved_without_starting_ai_run(
    monkeypatch, status, handoff_requested
):
    tenant_id, employee_id, conversation_id = uuid4(), uuid4(), uuid4()
    conversation = SimpleNamespace(
        id=conversation_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
        customer_name="Test Customer",
        customer_email=None,
        customer_phone=None,
        status=status,
        handoff_requested=handoff_requested,
    )
    db = _HandoffMessageDB()

    async def fake_get_conversation(*args, **kwargs):
        return conversation

    monkeypatch.setattr(
        customer_channel_service, "_get_conversation", fake_get_conversation
    )

    result_conversation, run = await customer_channel_service.send_message(
        db,
        conversation_id=conversation_id,
        token="valid-token",
        content="پیام پیگیری مشتری",
    )

    assert result_conversation is conversation
    assert run is None
    assert db.executed == 0
    assert db.flushed
    assert len(db.added) == 1
    saved_message = db.added[0]
    assert saved_message.tenant_id == tenant_id
    assert saved_message.conversation_id == conversation_id
    assert saved_message.role == "user"
    assert saved_message.content == "پیام پیگیری مشتری"
