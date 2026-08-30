from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
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

    service = UnifiedExecutionService(DispatchDb(work_item), agent_executor=FailingExecutor())

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

    service = UnifiedExecutionService(DispatchDb(work_item, foreign_agent), agent_executor=Executor())

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

    class Executor:
        async def dispatch(self, received_work_item, received_agent):
            assert received_work_item is work_item
            assert received_agent is agent
            return {"run_id": str(run_id), "employee_version_id": str(uuid4())}

    result = await UnifiedExecutionService(DispatchDb(work_item, agent), agent_executor=Executor()).dispatch(work_item)

    assert result.dispatched is True
    assert work_item.status is WorkItemStatus.RUNNING
    assert work_item.output_data["run_id"] == str(run_id)


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["success", "succeeded", "completed", "complete"])
async def test_agent_dispatch_completes_work_item_on_terminal_success(status):
    tenant_id = uuid4()
    agent_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="completed agent execution",
        status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT,
        executor_id=agent_id,
        input_data={"task": "finish"},
        policy_context={},
    )
    agent = SimpleNamespace(id=agent_id, tenant_id=tenant_id, enabled=True, status=AgentInstanceStatus.ENABLED)

    class Executor:
        async def dispatch(self, *_args):
            return {"status": status, "result": "done"}

    result = await UnifiedExecutionService(DispatchDb(work_item, agent), agent_executor=Executor()).dispatch(work_item)

    assert result.dispatched is True
    assert work_item.status is WorkItemStatus.SUCCEEDED
    assert work_item.output_data["status"] == status


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["failed", "failure", "error"])
async def test_agent_dispatch_fails_work_item_on_terminal_failure(status):
    tenant_id = uuid4()
    agent_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="failed agent execution",
        status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT,
        executor_id=agent_id,
        input_data={"task": "fail"},
        policy_context={},
    )
    agent = SimpleNamespace(id=agent_id, tenant_id=tenant_id, enabled=True, status=AgentInstanceStatus.ENABLED)

    class Executor:
        async def dispatch(self, *_args):
            return {"status": status, "error": "execution failed"}

    result = await UnifiedExecutionService(DispatchDb(work_item, agent), agent_executor=Executor()).dispatch(work_item)

    assert result.dispatched is True
    assert work_item.status is WorkItemStatus.FAILED
    assert work_item.output_data["status"] == status


@pytest.mark.asyncio
async def test_agent_dispatch_preserves_running_for_async_result():
    tenant_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="async agent execution",
        status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT,
        executor_id=agent_id,
        input_data={"task": "run"},
        policy_context={},
    )
    agent = SimpleNamespace(id=agent_id, tenant_id=tenant_id, enabled=True, status=AgentInstanceStatus.ENABLED)

    class Executor:
        async def dispatch(self, *_args):
            return {"run_id": str(run_id), "executor_type": "agent"}

    result = await UnifiedExecutionService(DispatchDb(work_item, agent), agent_executor=Executor()).dispatch(work_item)

    assert result.dispatched is True
    assert work_item.status is WorkItemStatus.RUNNING
    assert work_item.output_data["run_id"] == str(run_id)
