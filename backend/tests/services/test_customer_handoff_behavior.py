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


@pytest.mark.asyncio
async def test_public_chat_endpoint_handles_missing_run_during_handoff(monkeypatch):
    from app.api.v1 import public_chat
    from app.schemas.customer_channel import PublicMessageCreate

    conversation_id = uuid4()
    conversation = SimpleNamespace(id=conversation_id, status="human")

    async def fake_send_message(db, *, conversation_id, token, content):
        assert token == "customer-token"
        assert content == "please help"
        return conversation, None

    monkeypatch.setattr(
        public_chat.customer_channel_service, "send_message", fake_send_message
    )

    response = await public_chat.send_message(
        conversation_id=conversation_id,
        payload=PublicMessageCreate(content=" please help "),
        db=object(),
        x_customer_token="customer-token",
    )

    assert response.success is True
    assert response.data["conversation_id"] == conversation_id
    assert response.data["run_id"] is None
    assert response.data["status"] == "human"

class _ActiveRunResult:
    def __init__(self, count):
        self.count = count

    def scalar_one(self):
        return self.count


class _HandoffRequestDB:
    def __init__(self, active_runs=0):
        self.active_runs = active_runs
        self.added = []
        self.flushed = False

    async def execute(self, statement):
        return _ActiveRunResult(self.active_runs)

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        self.flushed = True


@pytest.mark.parametrize(
    "content",
    [
        "I want to talk to a human, please",
        "\u0644\u0637\u0641\u0627\u064b \u0628\u0627 \u06a9\u0627\u0631\u0634\u0646\u0627\u0633 \u0635\u062d\u0628\u062a \u06a9\u0646\u0645",
        "\u0645\u0646 \u0646\u06cc\u0627\u0632 \u0628\u0647 \u067e\u0634\u062a\u06cc\u0628\u0627\u0646 \u0627\u0646\u0633\u0627\u0646\u06cc \u062f\u0627\u0631\u0645",
    ],
)
def test_explicit_human_handoff_request_is_detected_from_current_message(content):
    assert customer_channel_service._is_explicit_human_handoff_request(content)


def test_prior_transcript_mention_does_not_trigger_handoff_without_current_request():
    assert not customer_channel_service._is_explicit_human_handoff_request(
        "Thanks, my current question is about delivery"
    )


@pytest.mark.asyncio
async def test_explicit_human_request_persists_handoff_and_does_not_start_ai_run(monkeypatch):
    tenant_id, employee_id, conversation_id = uuid4(), uuid4(), uuid4()
    conversation = SimpleNamespace(
        id=conversation_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
        customer_name="Test Customer",
        customer_email=None,
        customer_phone=None,
        status="open",
        handoff_requested=False,
        assigned_user_id=None,
    )
    db = _HandoffRequestDB()

    async def fake_get_conversation(*args, **kwargs):
        return conversation

    async def unexpected_create_run(*args, **kwargs):
        raise AssertionError("human handoff request must not create an AI Run")

    monkeypatch.setattr(customer_channel_service, "_get_conversation", fake_get_conversation)
    monkeypatch.setattr(customer_channel_service.run_service, "create_run", unexpected_create_run)

    result_conversation, run = await customer_channel_service.send_message(
        db,
        conversation_id=conversation_id,
        token="valid-token",
        content="\u0644\u0637\u0641\u0627\u064b \u0628\u0627 \u06a9\u0627\u0631\u0634\u0646\u0627\u0633 \u0635\u062d\u0628\u062a \u06a9\u0646\u0645",
    )

    assert result_conversation is conversation
    assert run is None
    assert conversation.handoff_requested is True
    assert conversation.assigned_user_id is None
    assert conversation.status == "human"
    assert db.flushed is True
    assert len(db.added) == 2
    assert db.added[0].role == "user"
    assert db.added[1].role == "assistant"
    assert "\u062b\u0628\u062a \u0634\u062f" in db.added[1].content
    assert "\u0632\u0645\u0627\u0646 \u067e\u0627\u0633\u062e" in db.added[1].content


@pytest.mark.asyncio
async def test_handoff_request_does_not_change_routing_while_ai_run_is_active(monkeypatch):
    from app.core.exceptions import ConflictError

    tenant_id, employee_id, conversation_id = uuid4(), uuid4(), uuid4()
    conversation = SimpleNamespace(
        id=conversation_id,
        tenant_id=tenant_id,
        employee_id=employee_id,
        customer_name="Test Customer",
        customer_email=None,
        customer_phone=None,
        status="open",
        handoff_requested=False,
        assigned_user_id=None,
    )
    db = _HandoffRequestDB(active_runs=1)

    async def fake_get_conversation(*args, **kwargs):
        return conversation

    monkeypatch.setattr(customer_channel_service, "_get_conversation", fake_get_conversation)

    with pytest.raises(ConflictError, match="current assistant response"):
        await customer_channel_service.send_message(
            db,
            conversation_id=conversation_id,
            token="valid-token",
            content="Please connect me to a human",
        )

    assert conversation.handoff_requested is False
    assert conversation.status == "open"
    assert db.added == []
    assert db.flushed is False

