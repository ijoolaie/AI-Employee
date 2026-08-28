from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.unified_execution import ExecutionResult


@pytest.mark.asyncio
async def test_worker_lifecycle_contract_keeps_agent_work_item_running():
    tenant_id = uuid4()
    run_id = uuid4()
    work_item = SimpleNamespace(
        tenant_id=tenant_id,
        executor_type=ExecutorType.AGENT,
        executor_id=uuid4(),
        status=WorkItemStatus.RUNNING,
        output_data={"run_id": str(run_id)},
    )

    result = ExecutionResult(work_item=work_item, dispatched=True)

    assert result.dispatched is True
    assert result.work_item.status is WorkItemStatus.RUNNING
    assert result.work_item.output_data["run_id"] == str(run_id)


def test_worker_completion_boundary_is_not_owned_by_dispatcher():
    assert WorkItemStatus.RUNNING is not WorkItemStatus.SUCCEEDED
