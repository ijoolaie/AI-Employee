from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.services import agent_policy_engine
from app.models.agent_access_review import AgentAccessReviewDecision
from app.services.agent_policy_engine import (
    PolicyDecision,
    PolicyRequest,
    authorize,
)


class FakeScalars:
    def __init__(self, value):
        self.value = value

    def first(self):
        return self.value


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalars(self):
        return FakeScalars(self.value)


class FakeDb:
    def __init__(self, instance, identity):
        self.instance = instance
        self.identity = identity

    async def execute(self, statement):
        text = str(statement)

        if "agent_kill_switches" in text:
            return FakeResult(None)

        if "agent_identities" in text:
            return FakeResult(self.identity)

        if "agent_access_reviews" in text:
            return FakeResult(
                SimpleNamespace(
                    decision=AgentAccessReviewDecision.APPROVED,
                    next_review_at=None,
                )
            )

        if "agent_instances" in text:
            return FakeResult(self.instance)

        return FakeResult(None)

    async def flush(self):
        pass


def request(tenant, agent):
    return PolicyRequest(
        tenant_id=tenant,
        agent_instance_id=agent,
        action="tool.execute",
        tool_name="send_email",
        required_permission=None,
        requires_approval=False,
        context={},
    )

@pytest.fixture
def no_kill_switch(monkeypatch):
    async def fake_assert_not_killed(*args, **kwargs):
        return None

    monkeypatch.setattr(
        agent_policy_engine,
        "assert_not_killed",
        fake_assert_not_killed,
    )

@pytest.mark.asyncio
async def test_policy_decision_calls_audit_bridge(
    monkeypatch,
    no_kill_switch,
):
    tenant = uuid4()

    instance = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        enabled=True,
        status=AgentInstanceStatus.ENABLED,
        permission_policy={
            "allowed_tools": ["send_email"],
            "permissions": [],
        },
    )

    identity = SimpleNamespace(
        id=uuid4(),
        active=True,
        revoked_at=None,
        expires_at=None,
    )

    captured = []

    async def fake_audit(db, decision):
        captured.append(decision)

    monkeypatch.setattr(
        agent_policy_engine,
        "record_policy_decision_audit",
        fake_audit,
    )

    result = await authorize(
        FakeDb(instance, identity),
        request(tenant, instance.id),
    )

    print(result.decision, result.reason)
    print(result.metadata)

    assert result.decision == PolicyDecision.ALLOW
    assert len(captured) == 1
    assert captured[0].action == "tool.execute"


@pytest.mark.asyncio
async def test_audit_bridge_failure_does_not_change_policy_behavior(
    monkeypatch,
    no_kill_switch,
):
    tenant = uuid4()

    instance = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        enabled=True,
        status=AgentInstanceStatus.ENABLED,
        permission_policy={
            "allowed_tools": ["send_email"],
            "permissions": [],
        },
    )

    identity = SimpleNamespace(
        id=uuid4(),
        active=True,
        revoked_at=None,
        expires_at=None,
    )

    async def failing_audit(db, decision):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr(
        agent_policy_engine,
        "record_policy_decision_audit",
        failing_audit,
    )

    with pytest.raises(RuntimeError):
        await authorize(
            FakeDb(instance, identity),
            request(tenant, instance.id),
        )