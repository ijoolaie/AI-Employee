from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.services.agent_policy_engine import (
    POLICY_VERSION,
    PolicyDecision,
    PolicyRequest,
    authorize,
)


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeDb:
    def __init__(self, *values):
        self.values = list(values)

    async def execute(self, _statement):
        return FakeResult(self.values.pop(0))

    async def flush(self):
        return None


def agent(**policy):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        enabled=True,
        status=AgentInstanceStatus.ENABLED,
        permission_policy=policy,
    )


def identity(**overrides):
    values = {"active": True, "revoked_at": None, "expires_at": None}
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_policy_allows_authorized_tool() -> None:
    tenant_id = uuid4()
    instance = agent(allowed_tools=["calculator"], permissions=["run.execute"])
    db = FakeDb(instance, identity())
    result = await authorize(db, PolicyRequest(tenant_id=tenant_id, agent_instance_id=instance.id, action="tool.execute", tool_name="calculator", required_permission="run.execute"))
    assert result.decision == PolicyDecision.ALLOW
    assert result.policy_version == POLICY_VERSION
    assert result.reason == "policy_allow"


@pytest.mark.asyncio
async def test_policy_denies_forbidden_tool() -> None:
    tenant_id = uuid4()
    instance = agent(allowed_tools=["calculator"], permissions=["run.execute"])
    db = FakeDb(instance, identity())
    result = await authorize(db, PolicyRequest(tenant_id=tenant_id, agent_instance_id=instance.id, action="tool.execute", tool_name="send_email", required_permission="run.execute"))
    assert result.decision == PolicyDecision.DENY
    assert result.reason == "tool_not_authorized"


@pytest.mark.asyncio
async def test_policy_requires_approval_before_high_risk_action() -> None:
    tenant_id = uuid4()
    instance = agent(allowed_tools=["send_email"], permissions=["run.execute"])
    db = FakeDb(instance, identity())
    result = await authorize(db, PolicyRequest(tenant_id=tenant_id, agent_instance_id=instance.id, action="tool.execute", tool_name="send_email", required_permission="run.execute", requires_approval=True))
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL
    assert result.reason == "human_approval_required"


@pytest.mark.asyncio
async def test_policy_denies_expired_identity() -> None:
    tenant_id = uuid4()
    instance = agent(allowed_tools=["calculator"], permissions=["run.execute"])
    db = FakeDb(instance, identity(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)))
    result = await authorize(db, PolicyRequest(tenant_id=tenant_id, agent_instance_id=instance.id, action="tool.execute", tool_name="calculator", required_permission="run.execute"))
    assert result.decision == PolicyDecision.DENY
    assert result.reason == "agent_identity_expired"
