from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


class HumanRuntime:
    def dispatch(self, work_item):
        return {"executor": "human", "work_item_id": str(work_item.id)}


class AgentRuntime:
    def dispatch(self, work_item, agent):
        return {"executor": "agent", "agent_id": str(agent.id)}


def work_item(tenant_id):
    return SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, status=WorkItemStatus.READY,
        executor_type=None, executor_id=None, output_data=None,
        policy_context={},
    )


def agent(tenant_id):
    return SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id, enabled=True,
        status=AgentInstanceStatus.ENABLED,
    )


def test_assign_human_and_dispatch():
    tenant_id = uuid4()
    item = work_item(tenant_id)
    service = UnifiedExecutionService(SimpleNamespace(get=lambda *_: None), human_executor=HumanRuntime())

    service.assign_human(item, uuid4())
    result = service.dispatch(item)

    assert result.dispatched is True
    assert item.executor_type is ExecutorType.HUMAN
    assert item.status is WorkItemStatus.SUCCEEDED


def test_cross_tenant_agent_is_rejected():
    service = UnifiedExecutionService(SimpleNamespace(get=lambda *_: None))
    item = work_item(uuid4())

    with pytest.raises(ExecutionError, match="cross-tenant"):
        service.assign_agent(item, agent(uuid4()))


def test_approval_gate_prevents_dispatch():
    tenant_id = uuid4()
    item = work_item(tenant_id)
    item.policy_context = {"requires_approval": True}
    service = UnifiedExecutionService(SimpleNamespace(get=lambda *_: None), human_executor=HumanRuntime())
    service.assign_human(item, uuid4())

    result = service.dispatch(item)

    assert result.dispatched is False
    assert result.waiting_for_approval is True
    assert item.status is WorkItemStatus.WAITING_APPROVAL


def test_agent_dispatch_is_tenant_scoped():
    tenant_id = uuid4()
    item = work_item(tenant_id)
    runtime_agent = agent(tenant_id)
    db = SimpleNamespace(get=lambda model, key: runtime_agent if key == runtime_agent.id else None)
    service = UnifiedExecutionService(db, agent_executor=AgentRuntime())

    service.assign_agent(item, runtime_agent)
    result = service.dispatch(item)

    assert result.dispatched is True
    assert item.status is WorkItemStatus.SUCCEEDED
    assert item.output_data["executor"] == "agent"
