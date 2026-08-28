from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.unified_execution import UnifiedExecutionService


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
