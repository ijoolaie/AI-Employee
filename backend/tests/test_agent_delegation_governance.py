from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.models.agent_instance import AgentInstanceStatus
from app.services import agent_policy_engine
from app.services.agent_policy_engine import PolicyDecision, PolicyRequest, authorize
from app.services.unified_execution import ExecutionError, UnifiedExecutionService
from app.models.work_item import ExecutorType, WorkItemStatus


class FakeResult:
    def __init__(self, value): self.value = value
    def scalar_one_or_none(self): return self.value
    def scalars(self): return self
    def first(self): return self.value


class FakeDb:
    def __init__(self, *values): self.values = list(values)
    async def execute(self, statement):
        if "agent_kill_switches" in str(statement):
            return FakeResult(None)
        return FakeResult(self.values.pop(0))
    async def flush(self): pass


def agent(tenant_id, agent_id=None, **policy):
    return SimpleNamespace(
        id=agent_id or uuid4(), tenant_id=tenant_id, enabled=True,
        status=AgentInstanceStatus.ENABLED, permission_policy=policy,
    )


def identity():
    return SimpleNamespace(active=True, revoked_at=None, expires_at=None)


@pytest.mark.asyncio
async def test_delegated_tool_requires_a_valid_delegation_proof(monkeypatch):
    tenant = uuid4(); target = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"])
    req = PolicyRequest(
        tenant_id=tenant, agent_instance_id=target.id, action="tool.execute",
        tool_name="send_email", required_permission="run.execute",
        delegation_id=uuid4(),
    )
    async def reject(*_args, **_kwargs):
        raise ValidationAppError("invalid")
    monkeypatch.setattr(agent_policy_engine, "validate_delegation", reject)
    result = await authorize(FakeDb(target, identity()), req)
    assert result.decision is PolicyDecision.DENY
    assert result.reason == "delegation_invalid"


@pytest.mark.asyncio
async def test_delegated_tool_is_allowed_only_when_scope_proof_valid(monkeypatch):
    tenant = uuid4(); target = agent(tenant, allowed_tools=["send_email"], permissions=["run.execute"])
    req = PolicyRequest(
        tenant_id=tenant, agent_instance_id=target.id, action="tool.execute",
        tool_name="send_email", required_permission="run.execute",
        delegation_id=uuid4(),
    )
    async def accept(*_args, **_kwargs): return SimpleNamespace(id=req.delegation_id)
    monkeypatch.setattr(agent_policy_engine, "validate_delegation", accept)
    result = await authorize(FakeDb(target, identity()), req)
    assert result.decision is PolicyDecision.ALLOW


def work_item(agent_id, tenant_id):
    return SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, title="parent", description=None,
        status=WorkItemStatus.RUNNING, priority=0, requester_id=None,
        executor_type=ExecutorType.AGENT, executor_id=agent_id,
        input_data={}, output_data={}, policy_context={},
    )


def test_direct_agent_to_agent_delegate_is_blocked():
    tenant = uuid4(); source = work_item(uuid4(), tenant)
    service = UnifiedExecutionService(SimpleNamespace(add=lambda _: None))
    with pytest.raises(ExecutionError, match="governed delegation authority"):
        service.delegate(source, actor_id=source.executor_id, target_type=ExecutorType.AGENT, target_id=uuid4())
