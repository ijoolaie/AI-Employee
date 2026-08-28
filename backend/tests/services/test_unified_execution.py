from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


@pytest.mark.asyncio
async def test_agent_dispatch_skips_duplicate_run_for_running_work_item():
    tenant_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="execute agent",
        status=WorkItemStatus.RUNNING,
        executor_type=ExecutorType.AGENT,
        executor_id=agent_id,
        input_data={},
        policy_context={},
        idempotency_key="agent-dispatch-1",
        output_data={"run_id": str(run_id), "executor_type": "agent"},
    )

    class FailingExecutor:
        async def dispatch(self, work_item, agent):
            raise AssertionError("duplicate agent execution must not create another Run")

    service = UnifiedExecutionService(
        SimpleNamespace(get=lambda *_args, **_kwargs: None),
        agent_executor=FailingExecutor(),
    )

    result = await service.dispatch(work_item)

    assert result.dispatched is False
    assert result.work_item.status is WorkItemStatus.RUNNING
    assert result.work_item.output_data["run_id"] == str(run_id)


@pytest.mark.asyncio
async def test_agent_dispatch_rejects_cross_tenant_agent_before_executor():
    tenant_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="cross tenant",
        status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT,
        executor_id=uuid4(),
        input_data={},
        policy_context={},
    )
    foreign_agent = SimpleNamespace(
        tenant_id=uuid4(),
        enabled=True,
        status=AgentInstanceStatus.ENABLED,
    )
    calls = []

    class Executor:
        async def dispatch(self, *_args):
            calls.append(True)
            return {"run_id": str(uuid4())}

    class Db:
        async def get(self, *_args):
            return foreign_agent

    service = UnifiedExecutionService(Db(), agent_executor=Executor())

    with pytest.raises(ExecutionError, match="agent executor is unavailable"):
        await service.dispatch(work_item)

    assert calls == []
    assert work_item.status is WorkItemStatus.FAILED


@pytest.mark.asyncio
async def test_agent_dispatch_passes_canonical_run_result_and_keeps_work_item_running():
    tenant_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="agent execution",
        status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT,
        executor_id=agent_id,
        input_data={"task": "triage"},
        policy_context={},
    )
    agent = SimpleNamespace(
        id=agent_id,
        tenant_id=tenant_id,
        enabled=True,
        status=AgentInstanceStatus.ENABLED,
    )

    class Db:
        async def get(self, *_args):
            return agent

    class Executor:
        async def dispatch(self, received_work_item, received_agent):
            assert received_work_item is work_item
            assert received_agent is agent
            return {"run_id": str(run_id), "employee_version_id": str(uuid4())}

    result = await UnifiedExecutionService(Db(), agent_executor=Executor()).dispatch(work_item)

    assert result.dispatched is True
    assert work_item.status is WorkItemStatus.RUNNING
    assert work_item.output_data["run_id"] == str(run_id)
