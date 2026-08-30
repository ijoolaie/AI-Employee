from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


class DispatchDb:
    def __init__(self, work_item, agent=None):
        self.work_item = work_item
        self.agent = agent

    async def execute(self, *_args):
        return SimpleNamespace(scalar_one_or_none=lambda: self.work_item)

    async def get(self, *_args):
        return self.agent

    async def flush(self):
        return None

    async def commit(self):
        return None


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


@pytest.mark.asyncio
async def test_assign_human_and_dispatch():
    tenant_id = uuid4()
    item = work_item(tenant_id)
    service = UnifiedExecutionService(DispatchDb(item), human_executor=HumanRuntime())

    service.assign_human(item, uuid4())
    result = await service.dispatch(item)

    assert result.dispatched is True
    assert item.executor_type is ExecutorType.HUMAN
    assert item.status is WorkItemStatus.RUNNING


@pytest.mark.asyncio
async def test_cross_tenant_agent_is_rejected():
    service = UnifiedExecutionService(SimpleNamespace(get=None))
    item = work_item(uuid4())

    with pytest.raises(ExecutionError, match="cross-tenant"):
        await service.assign_agent(item, agent(uuid4()))


@pytest.mark.asyncio
async def test_approval_gate_prevents_dispatch():
    tenant_id = uuid4()
    item = work_item(tenant_id)
    item.policy_context = {"requires_approval": True}
    service = UnifiedExecutionService(DispatchDb(item), human_executor=HumanRuntime())
    service.assign_human(item, uuid4())

    result = await service.dispatch(item)

    assert result.dispatched is False
    assert result.waiting_for_approval is True
    assert item.status is WorkItemStatus.WAITING_APPROVAL


@pytest.mark.asyncio
async def test_agent_dispatch_is_tenant_scoped():
    tenant_id = uuid4()
    item = work_item(tenant_id)
    runtime_agent = agent(tenant_id)
    service = UnifiedExecutionService(DispatchDb(item, runtime_agent), agent_executor=AgentRuntime())

    await service.assign_agent(item, runtime_agent)
    result = await service.dispatch(item)

    assert result.dispatched is True
    assert item.status is WorkItemStatus.RUNNING
    assert item.output_data["executor"] == "agent"
