from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.services.agent_policy_engine import PolicyDecision, PolicyRequest, assert_authorized, authorize


class Result:
    def __init__(self, value): self.value = value
    def scalar_one_or_none(self): return self.value
    def scalar_one(self): return self.value
    def scalars(self): return self
    def first(self): return self.value


class Db:
    def __init__(self, *values): self.values = list(values)
    async def execute(self, statement):
        if "agent_kill_switches" in str(statement):
            return Result(None)
        return Result(self.values.pop(0))
    async def flush(self): pass


def setup():
    tenant = uuid4()
    agent = SimpleNamespace(id=uuid4(), tenant_id=tenant, enabled=True, status=AgentInstanceStatus.ENABLED,
                            permission_policy={"allowed_tools": ["send_email"], "permissions": ["run.execute"]})
    identity = SimpleNamespace(id=uuid4(), active=True, revoked_at=None, expires_at=None)
    access_review = SimpleNamespace(id=uuid4(), reviewed_at=datetime.now(timezone.utc), next_review_at=None)
    request = PolicyRequest(tenant_id=tenant, agent_instance_id=agent.id, action="tool.execute",
                            tool_name="send_email", required_permission="run.execute",
                            run_id=uuid4(), tool_call_id="call-1", approval_request_id=uuid4(),
                            arguments={"to": ["allowed@example.com"], "subject": "x", "body": "y"},
                            approval_granted=True, requires_approval=True)
    return tenant, agent, identity, access_review, request


@pytest.mark.asyncio
@pytest.mark.parametrize("field,value", [
    ("tenant_id", uuid4()),
    ("run_id", uuid4()),
    ("tool_call_id", "wrong-call"),
    ("approval_request_id", uuid4()),
])
async def test_negative_approval_context_never_grants_access(field, value):
    tenant, agent, identity, access_review, request = setup()
    request = PolicyRequest(**{**request.__dict__, field: value})
    if field == "tool_call_id":
        approval = SimpleNamespace(id=request.approval_request_id, tenant_id=request.tenant_id,
                                   run_id=request.run_id, tool_name=request.tool_name,
                                   tool_call_id="call-1", arguments=request.arguments,
                                   status="approved")
        db = Db(agent, identity, access_review, approval)
        result = await authorize(db, request)
        assert result.decision == PolicyDecision.DENY
        assert result.reason == "approval_tool_call_mismatch"
    else:
        result = await authorize(Db(agent, identity, access_review, None), request)
        assert result.decision == PolicyDecision.REQUIRE_APPROVAL
        assert result.reason == "approval_not_found_or_not_approved"


@pytest.mark.asyncio
async def test_negative_missing_permission_is_denied():
    tenant, agent, identity, access_review, request = setup()
    agent.permission_policy = {"allowed_tools": ["send_email"], "permissions": []}
    result = await authorize(Db(agent, identity, access_review), request)
    assert result.decision == PolicyDecision.DENY
    assert result.reason == "permission_not_granted"


@pytest.mark.asyncio
async def test_negative_assert_authorized_fails_closed_for_missing_approval_artifact():
    tenant, agent, identity, access_review, request = setup()
    request = PolicyRequest(**{**request.__dict__, "approval_granted": False})
    with pytest.raises(ValidationAppError):
        await assert_authorized(Db(agent, identity, access_review, None), request)
