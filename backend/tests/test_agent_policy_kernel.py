from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.agent_access_review import AgentAccessReviewDecision
from app.models.agent_instance import AgentInstanceStatus
from app.services.agent_governance_freshness import execution_authority_fingerprint
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
    def __init__(self, *values, access_review="auto", template=None):
        self.values, self.flushed, self.access_review, self.template = list(values), False, access_review, template

    async def execute(self, statement):
        text = str(statement)
        if "agent_kill_switches" in text:
            return FakeResult(None)
        if "agent_templates" in text:
            return FakeResult(self.template)
        if "agent_access_reviews" in text:
            review = self.access_review
            if review == "auto":
                review = SimpleNamespace(
                    id=uuid4(),
                    agent_identity_id=None,
                    tenant_id=None,
                    decision=AgentAccessReviewDecision.APPROVED,
                    reviewed_at=datetime.now(timezone.utc),
                    next_review_at=None,
                )
            return FakeResult(review)
        if "agent_identities" in text:
            return FakeResult(self.values[1] if len(self.values) > 1 else None)
        if "agent_instances" in text:
            return FakeResult(self.values[0] if self.values else None)
        return FakeResult(self.values.pop(0))

    async def flush(self): self.flushed = True


def agent(tenant_id, **policy):
    return SimpleNamespace(id=uuid4(), tenant_id=tenant_id, enabled=True, status=AgentInstanceStatus.ENABLED, permission_policy=policy)


def governed_agent(tenant_id, template_id, **policy):
    instance = agent(tenant_id, **policy)
    instance.agent_template_id = template_id
    instance.agent_definition_id = None
    instance.configuration = {}
    instance.max_concurrency = 1
    instance.budget_policy = {}
    return instance


def identity(**overrides):
    values = {"id": uuid4(), "active": True, "revoked_at": None, "expires_at": None}; values.update(overrides); return SimpleNamespace(**values)


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


def published_template(template_id, tenant_id, definition_id=None):
    return SimpleNamespace(
        id=template_id,
        tenant_id=tenant_id,
        status=SimpleNamespace(value="published"),
        version=3,
        agent_definition_id=definition_id or uuid4(),
        risk_tier=2,
        capability_contract={"read": True},
        permission_policy={"allowed_tools": ["send_email"], "permissions": ["run.execute"]},
        approval_policy={"requires_ceo_approval": True},
        install_policy={"requires_ceo_approval": True},
    )


def apply_governance_fingerprint(instance, template, configuration=None):
    configuration = configuration or {}
    instance.configuration = {
        **configuration,
        "_governance_fingerprint": execution_authority_fingerprint(
            tenant_id=instance.tenant_id,
            template_id=template.id,
            template_version=template.version,
            agent_definition_id=template.agent_definition_id,
            risk_tier=template.risk_tier,
            capability_contract=template.capability_contract,
            permission_policy=template.permission_policy,
            approval_policy=template.approval_policy,
            install_policy=template.install_policy,
            configuration=configuration,
            max_concurrency=instance.max_concurrency,
            budget_policy=instance.budget_policy,
        ),
    }
    instance.agent_definition_id = template.agent_definition_id


@pytest.mark.asyncio
async def test_allow_requires_identity_access_review_tool_permission_and_exact_approval():
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
async def test_missing_access_review_is_denied_and_deactivated():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); active = identity()
    db = FakeDb(instance, active, access_review=None)
    result = await authorize(db, request(tenant, instance.id))
    assert result.decision == PolicyDecision.DENY and result.reason == "agent_access_review_missing"
    assert active.active is False and db.flushed is True


@pytest.mark.asyncio
async def test_non_approved_latest_access_review_is_denied_and_deactivated():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); active = identity()
    revoked_review = SimpleNamespace(
        id=uuid4(),
        decision=AgentAccessReviewDecision.REVOKED,
        reviewed_at=datetime.now(timezone.utc),
        next_review_at=None,
    )
    db = FakeDb(instance, active, access_review=revoked_review)
    result = await authorize(db, request(tenant, instance.id))
    assert result.decision == PolicyDecision.DENY and result.reason == "agent_access_review_not_approved"
    assert active.active is False and db.flushed is True


@pytest.mark.asyncio
async def test_expired_access_review_is_denied_and_deactivated():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); active = identity()
    review = SimpleNamespace(
        id=uuid4(),
        decision=AgentAccessReviewDecision.APPROVED,
        reviewed_at=datetime.now(timezone.utc),
        next_review_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    db = FakeDb(instance, active, access_review=review)
    result = await authorize(db, request(tenant, instance.id))
    assert result.decision == PolicyDecision.DENY and result.reason == "agent_access_review_expired"
    assert active.active is False and db.flushed is True


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
async def test_runtime_governance_fingerprint_allows_unchanged_instance():
    tenant = uuid4(); template = published_template(uuid4(), tenant); instance = governed_agent(tenant, template.id, allowed_tools=["send_email"], permissions=["run.execute"])
    apply_governance_fingerprint(instance, template)
    req = request(tenant, instance.id)
    result = await authorize(FakeDb(instance, identity(), approval(req), template=template), req)
    assert result.decision == PolicyDecision.ALLOW


@pytest.mark.asyncio
async def test_runtime_governance_fingerprint_denies_permission_drift():
    tenant = uuid4(); template = published_template(uuid4(), tenant); instance = governed_agent(tenant, template.id, allowed_tools=["send_email"], permissions=["run.execute"])
    apply_governance_fingerprint(instance, template)
    instance.permission_policy = {"allowed_tools": ["send_email", "delete_customer"], "permissions": ["run.execute", "customer.delete"]}
    req = request(tenant, instance.id)
    result = await authorize(FakeDb(instance, identity(), approval(req), template=template), req)
    assert result.decision == PolicyDecision.DENY and result.reason == "agent_governance_fingerprint_mismatch"


@pytest.mark.asyncio
async def test_runtime_governance_fingerprint_denies_budget_drift():
    tenant = uuid4(); template = published_template(uuid4(), tenant); instance = governed_agent(tenant, template.id, allowed_tools=["send_email"], permissions=["run.execute"])
    apply_governance_fingerprint(instance, template)
    instance.budget_policy = {"max_cost_usd": "999"}
    req = request(tenant, instance.id)
    result = await authorize(FakeDb(instance, identity(), approval(req), template=template), req)
    assert result.decision == PolicyDecision.DENY and result.reason == "agent_governance_fingerprint_mismatch"


@pytest.mark.asyncio
async def test_runtime_governance_fingerprint_requires_proof_for_governed_instance():
    tenant = uuid4(); template = published_template(uuid4(), tenant); instance = governed_agent(tenant, template.id, allowed_tools=["send_email"], permissions=["run.execute"])
    req = request(tenant, instance.id)
    result = await authorize(FakeDb(instance, identity(), approval(req), template=template), req)
    assert result.decision == PolicyDecision.DENY and result.reason == "agent_governance_fingerprint_missing"


@pytest.mark.asyncio
async def test_assert_authorized_raises_for_missing_approval():
    tenant = uuid4(); instance = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"]); req = request(tenant, instance.id)
    req = PolicyRequest(**{**req.__dict__, "approval_granted": False})
    with pytest.raises(ValidationAppError) as exc: await assert_authorized(FakeDb(instance, identity(), None), req)
    assert exc.value.details["reason"] == "agent_access_review_not_approved" or exc.value.details["reason"] == "approval_not_found_or_not_approved"
