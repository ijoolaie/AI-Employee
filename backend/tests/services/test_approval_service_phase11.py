from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.services import approval_service
from app.services.approval_service import ConflictError, NotFoundError


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class Db:
    def __init__(self, *results):
        self.results = list(results)
        self.added = []

    def add(self, value):
        self.added.append(value)

    async def execute(self, *_args, **_kwargs):
        return Result(self.results.pop(0))

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_approval_decision_approve_moves_run_to_pending_and_audits(monkeypatch):
    tenant_id, approval_id, run_id, user_id = uuid4(), uuid4(), uuid4(), uuid4()
    approval = SimpleNamespace(id=approval_id, tenant_id=tenant_id, run_id=run_id, tool_name="crm.lookup", status="pending", decided_by=None, decision_reason=None, decided_at=None, requested_by=uuid4())
    run = SimpleNamespace(id=run_id, tenant_id=tenant_id, status="waiting", error=None, request_id="req-11")
    audit = []

    async def record(*args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(approval_service.audit_service, "record", record)
    result = await approval_service.decide(Db(approval, run), approval_id=approval_id, tenant_id=tenant_id, decided_by=user_id, decision="approve", reason="safe", actor_type="user")

    assert result.status == "approved"
    assert run.status == "pending"
    assert run.error is None
    assert result.decided_by == user_id
    assert audit[-1]["action"] == "tool.approval_decided"


@pytest.mark.asyncio
async def test_requester_cannot_self_approve(monkeypatch):
    tenant_id, approval_id, run_id, user_id = uuid4(), uuid4(), uuid4(), uuid4()
    approval = SimpleNamespace(id=approval_id, tenant_id=tenant_id, run_id=run_id, tool_name="create_order", status="pending", decided_by=None, decision_reason=None, decided_at=None, requested_by=user_id)
    run = SimpleNamespace(id=run_id, tenant_id=tenant_id, status="waiting", error=None, request_id="req-self")

    with pytest.raises(ConflictError, match="cannot approve their own request"):
        await approval_service.decide(Db(approval, run), approval_id=approval_id, tenant_id=tenant_id, decided_by=user_id, decision="approve", reason="", actor_type="user")
    assert approval.status == "pending"
    assert run.status == "waiting"


@pytest.mark.asyncio
async def test_approval_decision_rejects_and_records_failure(monkeypatch):
    tenant_id = uuid4()
    approval = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, run_id=uuid4(), tool_name="payments.refund", status="pending", decided_by=None, decision_reason=None, decided_at=None, requested_by=uuid4())
    run = SimpleNamespace(id=approval.run_id, tenant_id=tenant_id, status="waiting", error=None, request_id=None)

    async def record(*args, **kwargs):
        return None

    monkeypatch.setattr(approval_service.audit_service, "record", record)
    result = await approval_service.decide(Db(approval, run), approval_id=approval.id, tenant_id=tenant_id, decided_by=uuid4(), decision="reject", reason="policy denied", actor_type="user")

    assert result.status == "rejected"
    assert run.status == "failed"
    assert run.error["code"] == "TOOL_APPROVAL_REJECTED"
    assert run.error["message"] == "policy denied"


@pytest.mark.asyncio
async def test_agent_approval_requires_explicit_delegation_policy():
    tenant_id, agent_id = uuid4(), uuid4()
    approval = SimpleNamespace(tool_name="crm.lookup")
    agent = SimpleNamespace(id=agent_id, tenant_id=tenant_id, enabled=True, status=AgentInstanceStatus.ENABLED, configuration={})

    with pytest.raises(ConflictError, match="not authorized"):
        await approval_service._authorize_agent_decision(Db(agent), agent_id=agent_id, tenant_id=tenant_id, approval=approval)


@pytest.mark.asyncio
async def test_agent_approval_is_tenant_scoped():
    with pytest.raises(NotFoundError, match="not found"):
        await approval_service._authorize_agent_decision(Db(None), agent_id=uuid4(), tenant_id=uuid4(), approval=SimpleNamespace(tool_name="crm.lookup"))


@pytest.mark.asyncio
async def test_create_request_preserves_requester_and_emits_one_audit_event(monkeypatch):
    tenant_id, run_id, requester_id = uuid4(), uuid4(), uuid4()
    run = SimpleNamespace(id=run_id, tenant_id=tenant_id, request_id="req-create", status="running", created_by=requester_id)
    audit = []

    async def record(*args, **kwargs):
        audit.append(kwargs)

    monkeypatch.setattr(approval_service.audit_service, "record", record)
    approval = await approval_service.create_request(
        Db(None),
        run=run,
        tool_name="create_order",
        tool_call_id="call-1",
        arguments={"x": 1},
        continuation_messages=[],
        requested_by=run.created_by,
    )

    assert approval.requested_by == requester_id
    assert run.status == "waiting"
    assert [item["action"] for item in audit] == ["tool.approval_requested"]


@pytest.mark.asyncio
async def test_approval_decision_rejects_unsupported_decision_before_lookup():
    with pytest.raises(ConflictError, match="unsupported approval decision"):
        await approval_service.decide(
            Db(),
            approval_id=uuid4(),
            tenant_id=uuid4(),
            decided_by=uuid4(),
            decision="maybe",
            reason=None,
            actor_type="user",
        )


@pytest.mark.asyncio
async def test_approval_decision_is_tenant_scoped():
    with pytest.raises(NotFoundError, match="Approval request not found"):
        await approval_service.decide(
            Db(None),
            approval_id=uuid4(),
            tenant_id=uuid4(),
            decided_by=uuid4(),
            decision="approve",
            reason=None,
            actor_type="user",
        )


@pytest.mark.asyncio
async def test_approval_decision_rejects_already_decided_request():
    tenant_id, approval_id = uuid4(), uuid4()
    approval = SimpleNamespace(
        id=approval_id,
        tenant_id=tenant_id,
        run_id=uuid4(),
        tool_name="crm.lookup",
        status="approved",
        decided_by=uuid4(),
        decision_reason="already approved",
        decided_at=None,
        requested_by=uuid4(),
    )

    with pytest.raises(ConflictError, match="already decided: approved"):
        await approval_service.decide(
            Db(approval),
            approval_id=approval_id,
            tenant_id=tenant_id,
            decided_by=uuid4(),
            decision="reject",
            reason="late rejection",
            actor_type="user",
        )
    assert approval.status == "approved"
