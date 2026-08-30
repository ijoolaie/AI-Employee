from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


@pytest.mark.asyncio
async def test_human_work_item_happy_path_assign_dispatch_complete():
    tenant_id = uuid4()
    human_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="human acceptance",
        status=WorkItemStatus.READY,
        input_data={},
        policy_context={},
        idempotency_key="phase-11-human-happy",
    )

    class HumanExecutor:
        async def dispatch(self, received):
            assert received is work_item
            return {"accepted": True, "correlation_id": str(received.id)}

    service = UnifiedExecutionService(SimpleNamespace(), human_executor=HumanExecutor())
    service.assign_human(work_item, human_id)

    dispatched = await service.dispatch(work_item)
    completed = service.complete_human(
        work_item,
        executor_id=human_id,
        output={"accepted": True, "result": "done"},
    )

    assert dispatched.dispatched is True
    assert dispatched.waiting_for_approval is False
    assert completed.status is WorkItemStatus.SUCCEEDED
    assert completed.output_data["result"] == "done"


@pytest.mark.asyncio
async def test_human_work_item_waits_for_approval_then_dispatches_after_approval():
    tenant_id = uuid4()
    human_id = uuid4()
    calls = []
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="approval acceptance",
        status=WorkItemStatus.READY,
        input_data={},
        policy_context={"requires_approval": True, "approved": False},
        idempotency_key="phase-11-human-approval",
    )

    class HumanExecutor:
        async def dispatch(self, received):
            calls.append(received.id)
            return {"accepted": True}

    service = UnifiedExecutionService(SimpleNamespace(), human_executor=HumanExecutor())
    service.assign_human(work_item, human_id)

    waiting = await service.dispatch(work_item)
    assert waiting.dispatched is False
    assert waiting.waiting_for_approval is True
    assert work_item.status is WorkItemStatus.WAITING_APPROVAL
    assert calls == []

    work_item.policy_context["approved"] = True
    work_item.status = WorkItemStatus.ASSIGNED
    resumed = await service.dispatch(work_item)

    assert resumed.dispatched is True
    assert resumed.waiting_for_approval is False
    assert len(calls) == 1


def test_human_completion_rejects_non_owner():
    tenant_id = uuid4()
    owner = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="ownership",
        status=WorkItemStatus.RUNNING,
        executor_type=ExecutorType.HUMAN,
        executor_id=owner,
        input_data={},
        policy_context={},
        idempotency_key="phase-11-human-owner",
    )

    service = UnifiedExecutionService(SimpleNamespace())

    with pytest.raises(ExecutionError, match="does not own"):
        service.complete_human(work_item, executor_id=uuid4())


@pytest.mark.asyncio
async def test_agent_dispatch_records_run_correlation_and_duplicate_is_idempotent():
    tenant_id = uuid4()
    agent_id = uuid4()
    run_id = uuid4()
    work_item = WorkItem(
        tenant_id=tenant_id,
        title="agent acceptance",
        status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT,
        executor_id=agent_id,
        input_data={},
        policy_context={},
        idempotency_key="phase-11-agent-run",
    )
    agent = SimpleNamespace(
        id=agent_id,
        tenant_id=tenant_id,
        enabled=True,
        status=AgentInstanceStatus.ENABLED,
    )
    calls = []

    class Db:
        async def get(self, *_args):
            return agent

    class AgentExecutor:
        async def dispatch(self, *_args):
            calls.append(True)
            return {"run_id": str(run_id)}

    service = UnifiedExecutionService(Db(), agent_executor=AgentExecutor())
    first = await service.dispatch(work_item)
    second = await service.dispatch(work_item)

    assert first.dispatched is True
    assert work_item.output_data["run_id"] == str(run_id)
    assert second.dispatched is False
    assert len(calls) == 1
