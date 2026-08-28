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


@pytest.mark.asyncio
async def test_assign_human_and_dispatch():
    tenant_id = uuid4()
    item = work_item(tenant_id)
    service = UnifiedExecutionService(SimpleNamespace(get=None), human_executor=HumanRuntime())

    service.assign_human(item, uuid4())
    result = await service.dispatch(item)

    assert result.dispatched is True
    assert item.executor_type is ExecutorType.HUMAN
    assert item.status is WorkItemStatus.SUCCEEDED


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
    service = UnifiedExecutionService(SimpleNamespace(get=None), human_executor=HumanRuntime())
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

    async def get_agent(model, key):
        return runtime_agent if key == runtime_agent.id else None

    service = UnifiedExecutionService(SimpleNamespace(get=get_agent), agent_executor=AgentRuntime())

    await service.assign_agent(item, runtime_agent)
    result = await service.dispatch(item)

    assert result.dispatched is True
    # Dispatch starts the runtime asynchronously; completion is recorded by the worker.
    assert item.status is WorkItemStatus.RUNNING
    assert item.output_data["executor"] == "agent"
