from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.services.agent_policy_engine import POLICY_VERSION, PolicyDecision, PolicyRequest, assert_authorized, authorize


class FakeResult:
    def __init__(self, value): self.value = value
    def scalar_one_or_none(self): return self.value
    def scalar_one(self):
        if self.value is None: raise AssertionError("expected a value")
        return self.value
    def scalars(self): return self
    def first(self): return self.value
    def all(self): return self.value if isinstance(self.value, list) else []


class FakeDb:
    def __init__(self, *values): self.values, self.flushed = list(values), False
    async def execute(self, statement):
        if "agent_kill_switches" in str(statement):
            return FakeResult(None)
        return FakeResult(self.values.pop(0))
    async def flush(self): self.flushed = True


def agent(tenant_id, **policy):
    return SimpleNamespace(id=uuid4(), tenant_id=tenant_id, enabled=True, status=AgentInstanceStatus.ENABLED, permission_policy=policy)


def identity(**overrides):
    values = {"active": True, "revoked_at": None, "expires_at": None}; values.update(overrides); return SimpleNamespace(**values)


def request(tenant_id, agent_id, **overrides):
    values = {
        "tenant_id": tenant_id, "agent_instance_id": agent_id, "action": "tool.execute",
        "tool_name": "send_email", "required_permission": "run.execute", "requires_approval": True,
        "run_id": uuid4(), "tool_call_id": "call-1", "approval_request_id": uuid4(),
        "arguments": {"to": ["allowed@example.com"], "subject": "x", "body": "y"},
        "approval_granted": True,
    }
    values.update(overrides); return PolicyRequest(**values)


def approval(req, **overrides):
    values = {"id": req.approval_request_id, "tenant_id": req.tenant_id, "run_id": req.run_id, "tool_name": req.tool_name,
              "tool_call_id": req.tool_call_id, "arguments": req.arguments, "status": "approved"}
    values.update(overrides); return SimpleNamespace(**values)


@pytest.mark.asyncio
async def test_allow_requires_identity_tool_permission_and_exact_approval():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); req = request(tenant, instance.id)
    result = await authorize(FakeDb(instance, identity(), approval(req)), req)
    assert result.decision == PolicyDecision.ALLOW
    assert result.policy_version == POLICY_VERSION


@pytest.mark.asyncio
async def test_cross_tenant_instance_is_not_resolved():
    tenant, other_tenant = uuid4(), uuid4(); instance = agent(other_tenant, allowed_tools=["send_email"], permissions=["run.execute"])
    with pytest.raises(NotFoundError): await authorize(FakeDb(None), request(tenant, instance.id))


@pytest.mark.asyncio
async def test_forbidden_tool_is_denied_before_approval():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["calculator"], permissions=["run.execute"])
    result = await authorize(FakeDb(instance, identity()), request(tenant, instance.id))
    assert result.decision == PolicyDecision.DENY and result.reason == "tool_not_authorized"


@pytest.mark.asyncio
async def test_missing_approval_is_not_allowed():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); req = request(tenant, instance.id)
    req = PolicyRequest(**{**req.__dict__, "approval_granted": False})
    result = await authorize(FakeDb(instance, identity(), None), req)
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL
    assert result.reason == "approval_not_found_or_not_approved"


@pytest.mark.asyncio
async def test_approval_argument_tampering_is_denied():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); req = request(tenant, instance.id)
    tampered = {**req.arguments, "body": "tampered"}
    result = await authorize(FakeDb(instance, identity(), approval(req)), PolicyRequest(**{**req.__dict__, "arguments": tampered}))
    assert result.decision == PolicyDecision.DENY and result.reason == "approval_arguments_mismatch"


@pytest.mark.asyncio
async def test_approval_tool_call_mismatch_is_denied():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); req = request(tenant, instance.id)
    result = await authorize(FakeDb(instance, identity(), approval(req)), PolicyRequest(**{**req.__dict__, "tool_call_id": "wrong-call"}))
    assert result.decision == PolicyDecision.DENY and result.reason == "approval_tool_call_mismatch"


@pytest.mark.asyncio
async def test_expired_identity_is_denied_and_deactivated():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); expired = identity(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
    db = FakeDb(instance, expired); result = await authorize(db, request(tenant, instance.id))
    assert result.decision == PolicyDecision.DENY and result.reason == "agent_identity_expired"; assert expired.active is False and db.flushed is True


@pytest.mark.asyncio
async def test_revoked_identity_is_denied():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); revoked = identity(revoked_at=datetime.now(timezone.utc))
    result = await authorize(FakeDb(instance, revoked), request(tenant, instance.id))
    assert result.decision == PolicyDecision.DENY and result.reason == "agent_identity_revoked"


@pytest.mark.asyncio
async def test_retired_agent_is_denied():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); instance.status = AgentInstanceStatus.RETIRED
    result = await authorize(FakeDb(instance, identity()), request(tenant, instance.id))
    assert result.decision == PolicyDecision.DENY and result.reason == "agent_instance_not_executable"


@pytest.mark.asyncio
async def test_assert_authorized_raises_for_missing_approval():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); req = request(tenant, instance.id)
    req = PolicyRequest(**{**req.__dict__, "approval_granted": False})
    with pytest.raises(ValidationAppError) as exc: await assert_authorized(FakeDb(instance, identity(), None), req)
    assert exc.value.details["reason"] == "approval_not_found_or_not_approved"
