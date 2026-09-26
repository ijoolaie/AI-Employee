from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.models.agent_access_review import AgentAccessReviewDecision
from app.services import agent_policy_engine
from app.services.agent_delegation_service import authorize_delegation, revoke_delegation, validate_delegation
from app.services.agent_policy_engine import PolicyDecision, PolicyRequest, authorize
from app.services.unified_execution import ExecutionError, UnifiedExecutionService
from app.models.work_item import ExecutorType, WorkItemStatus


class FakeResult:
    def __init__(self, value): self.value = value
    def scalar_one_or_none(self): return self.value
    def scalars(self): return self
    def all(self): return self.value if isinstance(self.value, list) else [self.value]
    def first(self): return self.value


class FakeDb:
    def __init__(self, *values): self.values = list(values)
    async def execute(self, statement):
        text = str(statement)
        if "agent_kill_switches" in text:
            return FakeResult(None)
        if "agent_access_reviews" in text:
            return FakeResult(self.values[2] if len(self.values) > 2 else None)
        if "tool_approval_requests" in text:
            return FakeResult(self.values[3] if len(self.values) > 3 else None)
        if "agent_identities" in text:
            return FakeResult(self.values[1] if len(self.values) > 1 else None)
        if "agent_instances" in text:
            return FakeResult(self.values[0] if self.values else None)
        return FakeResult(self.values.pop(0))
    async def flush(self): pass


def agent(tenant_id, agent_id=None, **policy):
    return SimpleNamespace(id=agent_id or uuid4(), tenant_id=tenant_id, enabled=True,
                           status=AgentInstanceStatus.ENABLED, permission_policy=policy)


def identity():
    return SimpleNamespace(id=uuid4(), active=True, revoked_at=None, expires_at=None)


def access_review():
    return SimpleNamespace(id=uuid4(), decision=AgentAccessReviewDecision.APPROVED,
                           reviewed_at=datetime.now(timezone.utc), next_review_at=None)


@pytest.mark.asyncio
async def test_delegated_tool_requires_a_valid_delegation_proof(monkeypatch):
    tenant = uuid4(); target = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"])
    req = PolicyRequest(tenant_id=tenant, agent_instance_id=target.id, action="tool.execute",
                        tool_name="send_email", required_permission="run.execute", delegation_id=uuid4())
    async def reject(*_args, **_kwargs): raise ValidationAppError("invalid")
    monkeypatch.setattr(agent_policy_engine, "validate_delegation", reject)
    result = await authorize(FakeDb(target, identity(), access_review()), req)
    assert result.decision is PolicyDecision.DENY
    assert result.reason == "delegation_invalid"


@pytest.mark.asyncio
async def test_delegated_tool_is_allowed_only_when_scope_proof_valid(monkeypatch):
    tenant = uuid4(); target = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"])
    req = PolicyRequest(tenant_id=tenant, agent_instance_id=target.id, action="tool.execute",
                        tool_name="send_email", required_permission="run.execute", delegation_id=uuid4())
    async def accept(*_args, **_kwargs): return SimpleNamespace(id=req.delegation_id)
    monkeypatch.setattr(agent_policy_engine, "validate_delegation", accept)
    result = await authorize(FakeDb(target, identity(), access_review()), req)
    assert result.decision is PolicyDecision.ALLOW


def work_item(agent_id, tenant_id):
    return SimpleNamespace(id=uuid4(), tenant_id=tenant_id, title="parent", description=None,
                           status=WorkItemStatus.RUNNING, priority=0, requester_id=None,
                           executor_type=ExecutorType.AGENT, executor_id=agent_id,
                           input_data={}, output_data={}, policy_context={},)


def test_direct_agent_to_agent_delegate_is_blocked():
    tenant = uuid4(); source = work_item(uuid4(), tenant)
    service = UnifiedExecutionService(SimpleNamespace(add=lambda _: None))
    with pytest.raises(ExecutionError, match="governed delegation authority"):
        service.delegate(source, actor_id=source.executor_id, target_type=ExecutorType.AGENT, target_id=uuid4())


class DelegationDb:
    def __init__(self, delegation, agents, identities, reviews, source=None, delegated=None):
        self.delegation = delegation
        self.agents = agents
        self.identities = identities
        self.reviews = reviews
        self.source = source
        self.delegated = delegated

    async def execute(self, statement):
        text = str(statement)
        if "agent_delegations" in text:
            return FakeResult(self.delegation)
        if "work_items" in text:
            return FakeResult(self.source if self.delegated is None else (self.source or self.delegated))
        if "agent_instances" in text:
            return FakeResult(self.agents)
        if "agent_identities" in text:
            return FakeResult(self.identities)
        if "agent_access_reviews" in text:
            return FakeResult(self.reviews.pop(0) if self.reviews else None)
        return FakeResult(None)


def delegation_record(tenant_id, delegator_id, delegate_id, expires_at):
    return SimpleNamespace(id=uuid4(), tenant_id=tenant_id, delegator_agent_instance_id=delegator_id,
                           delegate_agent_instance_id=delegate_id, source_work_item_id=uuid4(),
                           delegated_work_item_id=None, status="active", expires_at=expires_at,
                           chain_depth=1, max_chain_depth=3, scopes={"actions": ["run.execute"], "tools": []})


@pytest.mark.asyncio
async def test_chained_delegation_cannot_expand_parent_scope(monkeypatch):
    tenant = uuid4()
    delegator = agent(tenant, permissions=["run.execute", "financial.commitment"])
    delegate = agent(tenant, permissions=["run.execute", "financial.commitment"])
    source = SimpleNamespace(
        id=uuid4(), tenant_id=tenant, status=WorkItemStatus.RUNNING,
        executor_type=ExecutorType.AGENT, executor_id=delegator.id,
        policy_context={"delegated_from": str(uuid4()), "delegation_id": str(uuid4()), "delegation_depth": 1},
    )
    parent = SimpleNamespace(
        id=uuid4(), tenant_id=tenant,
        delegator_agent_instance_id=uuid4(), delegate_agent_instance_id=delegator.id,
        source_work_item_id=uuid4(), delegated_work_item_id=source.id,
        status="active", expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        chain_depth=1, max_chain_depth=3,
        scopes={"actions": ["run.execute"], "tools": []},
    )
    parent_id = UUID(source.policy_context["delegation_id"])
    parent.id = parent_id

    class ChainDb:
        async def execute(self, statement):
            text = str(statement)
            if "agent_delegations" in text:
                return FakeResult(parent)
            if "work_items" in text:
                return FakeResult(source)
            if "agent_instances" in text:
                return FakeResult([delegator, delegate])
            if "agent_identities" in text:
                left = identity(); left.agent_instance_id = delegator.id
                right = identity(); right.agent_instance_id = delegate.id
                return FakeResult([left, right])
            return FakeResult(None)

    async def audit(*_args, **_kwargs): pass
    monkeypatch.setattr("app.services.agent_delegation_service.audit_service.record", audit)

    with pytest.raises(ValidationAppError, match="expand the parent delegation scope"):
        await authorize_delegation(
            ChainDb(),
            tenant_id=tenant,
            delegator_agent_instance_id=delegator.id,
            delegate_agent_instance_id=delegate.id,
            source_work_item_id=source.id,
            scopes={"actions": ["financial.commitment"]},
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )


@pytest.mark.asyncio
async def test_chained_delegation_cannot_outlive_parent(monkeypatch):
    tenant = uuid4()
    delegator = agent(tenant, permissions=["run.execute"])
    delegate = agent(tenant, permissions=["run.execute"])
    parent_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    source = SimpleNamespace(
        id=uuid4(), tenant_id=tenant, status=WorkItemStatus.RUNNING,
        executor_type=ExecutorType.AGENT, executor_id=delegator.id,
        policy_context={"delegated_from": str(uuid4()), "delegation_id": str(uuid4()), "delegation_depth": 1},
    )
    parent = SimpleNamespace(
        id=UUID(source.policy_context["delegation_id"]), tenant_id=tenant,
        delegator_agent_instance_id=uuid4(), delegate_agent_instance_id=delegator.id,
        source_work_item_id=uuid4(), delegated_work_item_id=source.id,
        status="active", expires_at=parent_expiry,
        chain_depth=1, max_chain_depth=3,
        scopes={"actions": ["run.execute"], "tools": []},
    )

    class ChainDb:
        async def execute(self, statement):
            text = str(statement)
            if "agent_delegations" in text:
                return FakeResult(parent)
            if "work_items" in text:
                return FakeResult(source)
            return FakeResult(None)

    async def audit(*_args, **_kwargs): pass
    monkeypatch.setattr("app.services.agent_delegation_service.audit_service.record", audit)

    with pytest.raises(ValidationAppError, match="outlive its parent"):
        await authorize_delegation(
            ChainDb(),
            tenant_id=tenant,
            delegator_agent_instance_id=delegator.id,
            delegate_agent_instance_id=delegate.id,
            source_work_item_id=source.id,
            scopes={"actions": ["run.execute"]},
            expires_at=parent_expiry + timedelta(minutes=1),
        )


@pytest.mark.asyncio
async def test_delegation_creation_locks_and_rejects_cancelled_source(monkeypatch):
    tenant = uuid4()
    delegator = agent(tenant, permissions=["run.execute"])
    delegate = agent(tenant, permissions=["run.execute"])
    source = SimpleNamespace(
        id=uuid4(), tenant_id=tenant, status=WorkItemStatus.CANCELLED,
        executor_type=ExecutorType.AGENT, executor_id=delegator.id,
        policy_context={},
    )
    statements = []

    class CreateDb:
        def add(self, _value): pass
        async def execute(self, statement):
            statements.append(str(statement))
            if "work_items" in str(statement):
                return FakeResult(source)
            if "agent_instances" in str(statement):
                return FakeResult([delegator, delegate])
            if "agent_identities" in str(statement):
                delegator_identity = identity(); delegator_identity.agent_instance_id = delegator.id
                delegate_identity = identity(); delegate_identity.agent_instance_id = delegate.id
                return FakeResult([delegator_identity, delegate_identity])
            return FakeResult(None)
        async def flush(self): pass

    async def audit(*_args, **_kwargs): pass
    monkeypatch.setattr("app.services.agent_delegation_service.audit_service.record", audit)

    with pytest.raises(ValidationAppError, match="cancelled source work item"):
        await authorize_delegation(
            CreateDb(),
            tenant_id=tenant,
            delegator_agent_instance_id=delegator.id,
            delegate_agent_instance_id=delegate.id,
            source_work_item_id=source.id,
            scopes={"actions": ["run.execute"]},
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

    assert statements
    assert "FOR UPDATE" in statements[0]


@pytest.mark.asyncio
async def test_delegation_is_denied_when_delegate_access_review_is_revoked():
    tenant = uuid4(); delegator = agent(tenant, permissions=["run.execute"]); delegate = agent(tenant, permissions=["run.execute"])
    delegation = delegation_record(tenant, delegator.id, delegate.id, datetime.now(timezone.utc) + timedelta(hours=1))
    delegator_identity = identity(); delegator_identity.agent_instance_id = delegator.id
    delegate_identity = identity(); delegate_identity.agent_instance_id = delegate.id
    approved = access_review(); revoked = access_review(); revoked.decision = AgentAccessReviewDecision.REVOKED
    source = SimpleNamespace(id=delegation.source_work_item_id, tenant_id=tenant, status=WorkItemStatus.RUNNING)
    db = DelegationDb(delegation, [delegator, delegate], [delegator_identity, delegate_identity], [approved, revoked], source=source)
    with pytest.raises(ValidationAppError, match="latest Access Review"):
        await validate_delegation(db, tenant_id=tenant, delegation_id=delegation.id, delegate_agent_instance_id=delegate.id)


@pytest.mark.asyncio
async def test_delegation_is_denied_when_delegator_identity_is_revoked():
    tenant = uuid4(); delegator = agent(tenant, permissions=["run.execute"]); delegate = agent(tenant, permissions=["run.execute"])
    delegation = delegation_record(tenant, delegator.id, delegate.id, datetime.now(timezone.utc) + timedelta(hours=1))
    delegator_identity = identity(); delegator_identity.agent_instance_id = delegator.id; delegator_identity.active = False
    delegate_identity = identity(); delegate_identity.agent_instance_id = delegate.id
    source = SimpleNamespace(id=delegation.source_work_item_id, tenant_id=tenant, status=WorkItemStatus.RUNNING)
    db = DelegationDb(delegation, [delegator, delegate], [delegator_identity, delegate_identity], [], source=source)
    with pytest.raises(ValidationAppError, match="currently active Agent identities"):
        await validate_delegation(db, tenant_id=tenant, delegation_id=delegation.id, delegate_agent_instance_id=delegate.id)


@pytest.mark.asyncio
async def test_delegation_is_denied_when_delegator_identity_is_expired():
    tenant = uuid4(); delegator = agent(tenant, permissions=["run.execute"]); delegate = agent(tenant, permissions=["run.execute"])
    delegation = delegation_record(tenant, delegator.id, delegate.id, datetime.now(timezone.utc) + timedelta(hours=1))
    delegator_identity = identity(); delegator_identity.agent_instance_id = delegator.id; delegator_identity.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    delegate_identity = identity(); delegate_identity.agent_instance_id = delegate.id
    source = SimpleNamespace(id=delegation.source_work_item_id, tenant_id=tenant, status=WorkItemStatus.RUNNING)
    db = DelegationDb(delegation, [delegator, delegate], [delegator_identity, delegate_identity], [], source=source)
    with pytest.raises(ValidationAppError, match="identity has expired"):
        await validate_delegation(db, tenant_id=tenant, delegation_id=delegation.id, delegate_agent_instance_id=delegate.id)


@pytest.mark.asyncio
async def test_delegated_run_dispatch_requires_and_persists_delegation_proof(monkeypatch):
    from app.services.agent_execution_adapter import AgentExecutionAdapter

    tenant = uuid4()
    agent_id = uuid4()
    delegation_id = uuid4()
    agent_obj = SimpleNamespace(
        id=agent_id, tenant_id=tenant, enabled=True,
        configuration={}, permission_policy={"allowed_tools": ["send_email"], "permissions": ["run.execute"]},
    )
    work = SimpleNamespace(
        id=uuid4(), tenant_id=tenant, executor_id=agent_id,
        policy_context={"delegated_from": str(uuid4()), "delegation_id": str(delegation_id)},
        input_data={}, requester_id=None,
    )
    captured = {}

    async def fake_authorize(_db, request):
        captured["request"] = request
        return SimpleNamespace(decision=PolicyDecision.ALLOW)

    async def fake_resolve(*_args, **_kwargs):
        return agent_obj, SimpleNamespace(id=uuid4()), SimpleNamespace(id=uuid4(), employee_id=uuid4())

    class Ctx:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return False

    class FakeDb:
        def begin_nested(self): return Ctx()
        async def flush(self): pass

    class FakeRun:
        id = uuid4()
        agent_instance_id = None
        delegation_id = None

    created_run = FakeRun()
    async def fake_create_run(*_args, **_kwargs): return created_run
    async def fake_enqueue(*_args, **_kwargs): pass

    import app.services.agent_execution_adapter as mod
    monkeypatch.setattr(mod, "assert_authorized", fake_authorize)
    monkeypatch.setattr(mod, "resolve_employee_version", fake_resolve)
    monkeypatch.setattr(mod, "create_run", fake_create_run)
    monkeypatch.setattr(mod.outbox_service, "enqueue", fake_enqueue)

    result = await AgentExecutionAdapter(FakeDb()).dispatch(work, agent_obj)

    assert captured["request"].delegation_id == delegation_id
    assert created_run.delegation_id == delegation_id
    assert result["executor_type"] == "agent"


@pytest.mark.asyncio
async def test_delegated_tool_policy_receives_delegation_proof(monkeypatch):
    from app.services import agent_tool_governance

    tenant, agent_id, run_id, delegation_id = uuid4(), uuid4(), uuid4(), uuid4()
    captured = {}

    class FakeDb:
        async def execute(self, _statement):
            return FakeResult(None)
        async def flush(self): pass

    async def fake_authorize(_db, request):
        captured["request"] = request
        return SimpleNamespace(decision=PolicyDecision.ALLOW)

    monkeypatch.setattr(agent_tool_governance, "assert_authorized", fake_authorize)

    async with agent_tool_governance.agent_tool_context(
        tenant_id=tenant,
        agent_instance_id=agent_id,
        run_id=run_id,
        delegation_id=delegation_id,
    ):
        await agent_tool_governance.registry.execute(
            "calculator",
            {"expression": "1+1"},
            db=FakeDb(),
            tenant_id=tenant,
            permissions={"run.execute"},
            allowed_tools={"calculator"},
        )

    assert captured["request"].delegation_id == delegation_id



@pytest.mark.asyncio
async def test_validate_delegation_locks_authority_row_before_work_item_state():
    tenant = uuid4()
    delegator = uuid4()
    delegate = uuid4()
    delegation = delegation_record(tenant, delegator, delegate, datetime.now(timezone.utc) + timedelta(hours=1))
    delegation.source_work_item_id = uuid4()
    source = SimpleNamespace(id=delegation.source_work_item_id, tenant_id=tenant, status=WorkItemStatus.RUNNING)
    delegator_agent = agent(tenant, delegator, permissions=["run.execute"])
    delegate_agent = agent(tenant, delegate, permissions=["run.execute"])
    left = identity(); left.agent_instance_id = delegator
    right = identity(); right.agent_instance_id = delegate
    statements = []

    class LockDb(DelegationDb):
        async def execute(self, statement):
            statements.append(str(statement))
            return await super().execute(statement)

    db = LockDb(
        delegation,
        [delegator_agent, delegate_agent],
        [left, right],
        [access_review(), access_review()],
        source=source,
    )
    result = await validate_delegation(
        db,
        tenant_id=tenant,
        delegation_id=delegation.id,
        delegate_agent_instance_id=delegate,
        action="run.execute",
    )
    assert result.id == delegation.id
    assert "FOR UPDATE" in statements[0]


@pytest.mark.asyncio
async def test_revoke_delegation_is_idempotently_rejected_after_first_revoke(monkeypatch):
    tenant = uuid4()
    delegator = uuid4()
    delegate = uuid4()
    delegation = delegation_record(
        tenant,
        delegator,
        delegate,
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    calls = []

    class RevokeDb:
        async def execute(self, statement):
            calls.append(str(statement))
            return FakeResult(delegation)
        async def flush(self):
            pass

    async def audit(*_args, **_kwargs):
        pass

    monkeypatch.setattr("app.services.agent_delegation_service.audit_service.record", audit)
    db = RevokeDb()

    result = await revoke_delegation(
        db,
        tenant_id=tenant,
        delegation_id=delegation.id,
        actor_user_id=uuid4(),
    )
    assert result.status == "revoked"
    assert "FOR UPDATE" in calls[0]

    with pytest.raises(ValidationAppError, match="not active"):
        await revoke_delegation(
            db,
            tenant_id=tenant,
            delegation_id=delegation.id,
            actor_user_id=uuid4(),
        )
