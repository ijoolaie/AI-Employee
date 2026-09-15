from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.services.agent_policy_engine import PolicyDecision, PolicyRequest, authorize


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeDb:
    def __init__(self, identity):
        self.identity = identity

    async def execute(self, statement):
        text = str(statement)
        if "agent_identities" in text:
            return FakeResult(self.identity)
        if "agent_instances" in text:
            return FakeResult(SimpleNamespace(
                id=self.identity.agent_instance_id,
                tenant_id=self.identity.tenant_id,
                enabled=True,
                status=AgentInstanceStatus.ENABLED,
                permission_policy={"allowed_tools": ["send_email"], "permissions": []},
            ))
        if "agent_access_reviews" in text:
            from app.models.agent_access_review import AgentAccessReviewDecision
            return FakeResult(SimpleNamespace(decision=AgentAccessReviewDecision.APPROVED, next_review_at=None))
        return FakeResult(None)

    async def flush(self):
        pass


@pytest.mark.asyncio
async def test_revoked_identity_fails_closed():
    tenant = uuid4()
    identity = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        agent_instance_id=uuid4(),
        active=False,
        revoked_at="revoked",
        expires_at=None,
    )

    result = await authorize(
        FakeDb(identity),
        PolicyRequest(
            tenant_id=tenant,
            agent_instance_id=identity.agent_instance_id,
            action="tool.execute",
            tool_name="send_email",
        ),
    )

    assert result.decision == PolicyDecision.DENY
    assert result.reason == "agent_identity_revoked"
