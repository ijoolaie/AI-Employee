from types import SimpleNamespace
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_enqueue_persists_active_agent_binding(monkeypatch):
    from app.services import agent_tool_governance, outbox_service

    tenant_id = uuid4()
    agent_instance_id = uuid4()
    run_id = uuid4()
    monkeypatch.setattr(
        agent_tool_governance,
        "current_agent_tool_context",
        lambda: (tenant_id, agent_instance_id, run_id, "send_email"),
    )

    class FakeDB:
        def add(self, row):
            self.row = row

        async def flush(self):
            self.row.id = uuid4()

    db = FakeDB()
    row = await outbox_service.enqueue(
        db,
        kind="email.send",
        tenant_id=tenant_id,
        payload={"to": ["user@example.com"], "subject": "x", "body": "y"},
    )

    assert row.payload["_agent_governance"] == {
        "tenant_id": str(tenant_id),
        "agent_instance_id": str(agent_instance_id),
        "run_id": str(run_id),
        "tool_name": "send_email",
    }


@pytest.mark.asyncio
async def test_email_worker_reauthorizes_agent_before_smtp(monkeypatch):
    from app.workers import email_worker

    tenant_id = uuid4()
    agent_instance_id = uuid4()
    run_id = uuid4()
    row = SimpleNamespace(
        tenant_id=tenant_id,
        payload={
            "to": ["user@example.com"],
            "subject": "x",
            "body": "y",
            "_agent_governance": {
                "tenant_id": str(tenant_id),
                "agent_instance_id": str(agent_instance_id),
                "run_id": str(run_id),
                "tool_name": "send_email",
            },
        },
    )
    calls = []

    async def fake_authorize(db, request):
        calls.append(request)

    monkeypatch.setattr(email_worker, "assert_authorized", fake_authorize)
    await email_worker._authorize_deferred_agent_side_effect(object(), row)

    assert len(calls) == 1
    assert calls[0].tenant_id == tenant_id
    assert calls[0].agent_instance_id == agent_instance_id
    assert calls[0].run_id == run_id
    assert calls[0].action == "tool.execute"
    assert calls[0].tool_name == "send_email"
    assert calls[0].required_permission == "run.execute"
    assert calls[0].requires_approval is False


@pytest.mark.asyncio
async def test_email_worker_fails_closed_on_malformed_agent_binding():
    from app.core.exceptions import ValidationAppError
    from app.workers.email_worker import _authorize_deferred_agent_side_effect

    row = SimpleNamespace(
        tenant_id=uuid4(),
        payload={"_agent_governance": {"tool_name": "send_email"}},
    )
    with pytest.raises(ValidationAppError, match="Malformed Agent outbox governance binding"):
        await _authorize_deferred_agent_side_effect(object(), row)


@pytest.mark.asyncio
async def test_email_worker_rejects_cross_tenant_agent_binding():
    from app.core.exceptions import ValidationAppError
    from app.workers.email_worker import _authorize_deferred_agent_side_effect

    row = SimpleNamespace(
        tenant_id=uuid4(),
        payload={
            "_agent_governance": {
                "tenant_id": str(uuid4()),
                "agent_instance_id": str(uuid4()),
                "run_id": str(uuid4()),
                "tool_name": "send_email",
            }
        },
    )
    with pytest.raises(ValidationAppError, match="Agent outbox governance binding mismatch"):
        await _authorize_deferred_agent_side_effect(object(), row)
