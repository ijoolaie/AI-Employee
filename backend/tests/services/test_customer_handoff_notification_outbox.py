from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services import customer_channel_service


@pytest.mark.asyncio
async def test_handoff_uses_configured_destination_and_tenant_dedupe(monkeypatch):
    tenant_id, conversation_id, channel_id = uuid4(), uuid4(), uuid4()
    conversation = SimpleNamespace(
        id=conversation_id, tenant_id=tenant_id, employee_id=uuid4(),
        channel_id=channel_id, customer_name=None, customer_email=None,
        customer_phone=None, status="open", handoff_requested=False,
        assigned_user_id=None,
    )
    class DB:
        def __init__(self):
            self.added = []
        def add(self, row):
            self.added.append(row)
        async def flush(self):
            pass
        async def execute(self, statement):
            raise AssertionError("handoff must not create an AI run")
    db = DB()
    calls = []
    async def get_conversation(*args, **kwargs):
        return conversation
    async def enqueue(db_arg, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(id=uuid4())
    monkeypatch.setattr(customer_channel_service, "_get_conversation", get_conversation)
    monkeypatch.setattr(customer_channel_service, "get_settings", lambda: SimpleNamespace(
        customer_handoff_notification_email="ops"
    ))
    monkeypatch.setattr(customer_channel_service.outbox_service, "enqueue", enqueue)
    result, run = await customer_channel_service.send_message(
        db, conversation_id=conversation_id, token="token", content="Please connect me to a human"
    )
    assert result is conversation and run is None
    assert conversation.status == "human"
    assert len(calls) == 1
    assert calls[0]["tenant_id"] == tenant_id
    assert calls[0]["kind"] == "email.send"
    assert calls[0]["dedupe_key"] == f"customer-handoff:{conversation_id}"
    assert calls[0]["payload"]["to"] == ["ops"]
    assert str(channel_id) in calls[0]["payload"]["body"]
    assert len(db.added) == 2
