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

    async def execute(self, *_args, **_kwargs):
        return Result(self.results.pop(0))

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_approval_decision_approve_moves_run_to_pending_and_audits(monkeypatch):
    tenant_id = uuid4()
    approval_id = uuid4()
    run_id = uuid4()
    user_id = uuid4()
    approval = SimpleNamespace(
        id=approval_id, tenant_id=tenant_id, run_id=run_id, tool_name="crm.lookup",
        status="pending", decided_by=None, decision_reason=None, decided_at=None,
    )
    run = SimpleNamespace(id=run_id, tenant_id=tenant_id, status="waiting", error=None, request_id="req-11")
    audit = []
    monkeypatch.setattr(approval_service.audit_service, "record", lambda *args, **kwargs: audit.append(kwargs))

    result = await approval_service.decide(
        Db(approval, run), approval_id=approval_id, tenant_id=tenant_id,
        decided_by=user_id, decision="approve", reason="safe", actor_type="user",
    )

    assert result.status == "approved"
    assert run.status == "pending"
    assert run.error is None
    assert result.decided_by == user_id
    assert audit[-1]["action"] == "tool.approval_decided"


@pytest.mark.asyncio
async def test_approval_decision_rejects_and_records_failure(monkeypatch):
    tenant_id = uuid4()
    approval = SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, run_id=uuid4(), tool_name="payments.refund",
        status="pending", decided_by=None, decision_reason=None, decided_at=None,
    )
    run = SimpleNamespace(id=approval.run_id, tenant_id=tenant_id, status="waiting", error=None, request_id=None)
    monkeypatch.setattr(approval_service.audit_service, "record", lambda *args, **kwargs: None)

    result = await approval_service.decide(
        Db(approval, run), approval_id=approval.id, tenant_id=tenant_id,
        decided_by=uuid4(), decision="reject", reason="policy denied", actor_type="user",
    )

    assert result.status == "rejected"
    assert run.status == "failed"
    assert run.error["code"] == "TOOL_APPROVAL_REJECTED"
    assert run.error["message"] == "policy denied"


@pytest.mark.asyncio
async def test_agent_approval_requires_explicit_delegation_policy():
    tenant_id = uuid4()
    agent_id = uuid4()
    approval = SimpleNamespace(tool_name="crm.lookup")
    agent = SimpleNamespace(
        id=agent_id, tenant_id=tenant_id, enabled=True,
        status=AgentInstanceStatus.ENABLED, configuration={},
    )

    with pytest.raises(ConflictError, match="not authorized"):
        await approval_service._authorize_agent_decision(
            Db(agent), agent_id=agent_id, tenant_id=tenant_id, approval=approval,
        )


@pytest.mark.asyncio
async def test_agent_approval_is_tenant_scoped():
    with pytest.raises(NotFoundError, match="not found"):
        await approval_service._authorize_agent_decision(
            Db(None), agent_id=uuid4(), tenant_id=uuid4(), approval=SimpleNamespace(tool_name="crm.lookup"),
        )
