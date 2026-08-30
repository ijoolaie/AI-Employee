from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.unified_execution import UnifiedExecutionService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("result_status", "expected"),
    [
        ("succeeded", WorkItemStatus.SUCCEEDED),
        ("completed", WorkItemStatus.SUCCEEDED),
        ("failed", WorkItemStatus.FAILED),
        ("error", WorkItemStatus.FAILED),
    ],
)
async def test_agent_dispatch_maps_explicit_terminal_result(result_status, expected):
    tenant_id = uuid4()
    agent_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="agent completion",
        status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT,
        executor_id=agent_id,
        input_data={},
        policy_context={},
        idempotency_key=f"agent-completion-{result_status}",
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

    class AgentExecutor:
        async def dispatch(self, *_args):
            return {"status": result_status, "result": "done"}

    service = UnifiedExecutionService(Db(), agent_executor=AgentExecutor())
    result = await service.dispatch(work_item)

    assert result.dispatched is True
    assert work_item.status is expected
    assert work_item.output_data["result"] == "done"


@pytest.mark.asyncio
async def test_agent_dispatch_keeps_async_result_running():
    tenant_id = uuid4()
    agent_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="agent async completion",
        status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT,
        executor_id=agent_id,
        input_data={},
        policy_context={},
        idempotency_key="agent-completion-running",
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

    class AgentExecutor:
        async def dispatch(self, *_args):
            return {"run_id": str(uuid4())}

    service = UnifiedExecutionService(Db(), agent_executor=AgentExecutor())
    await service.dispatch(work_item)

    assert work_item.status is WorkItemStatus.RUNNING
