from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.contracts.agent_identity import AgentIdentityLifecycleAction
from app.services import agent_identity_lifecycle


@pytest.mark.asyncio
async def test_identity_lifecycle_revoke_emits_audit(monkeypatch):
    tenant = uuid4()
    instance_id = uuid4()
    identity = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        agent_instance_id=instance_id,
        active=True,
        revoked_at=None,
    )

    captured = []

    async def fake_record(db, **kwargs):
        captured.append(kwargs)

    monkeypatch.setattr(
        agent_identity_lifecycle.audit_service,
        "record",
        fake_record,
    )

    await agent_identity_lifecycle.apply_identity_lifecycle(
        None,
        identity,
        AgentIdentityLifecycleAction.REVOKE,
        reason="security review",
    )

    assert identity.active is False
    assert identity.revoked_at is not None
    assert len(captured) == 1
    assert captured[0]["action"] == "agent.identity.lifecycle"
    assert captured[0]["status"] == "revoke"
    assert captured[0]["tenant_id"] == tenant
