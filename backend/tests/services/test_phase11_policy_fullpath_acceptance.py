"""Full-path policy and tenant acceptance evidence for Phase 11 Unified Execution."""

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.agent_instance import AgentInstanceStatus
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.execution_policy import ExecutionPolicyError
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


class DispatchDb:
    def __init__(self, work_item, agent=None):
        self.work_item = work_item
        self.agent = agent
        self.commits = 0

    async def execute(self, *_args):
        return SimpleNamespace(scalar_one_or_none=lambda: self.work_item)

    async def get(self, *_args):
        return self.agent

    async def flush(self):
        return None

    async def commit(self):
        self.commits += 1


def make_agent_work_item(policy_context):
    tenant_id = uuid4()
    agent_id = uuid4()
    item = WorkItem(
        tenant_id=tenant_id,
        title="policy acceptance",
        status=WorkItemStatus.ASSIGNED,
        executor_type=ExecutorType.AGENT,
        executor_id=agent_id,
        input_data={},
        policy_context=policy_context,
        idempotency_key=f"phase11-policy-{uuid4()}",
    )
    agent = SimpleNamespace(
        id=agent_id,
        tenant_id=tenant_id,
        enabled=True,
        status=AgentInstanceStatus.ENABLED,
    )
    return item, agent


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "policy_context,error",
    [
        ({"required_capability": "deploy", "capabilities": []}, "required capability"),
        ({"tool": "shell", "allowed_tools": []}, "tool is outside"),
        ({"budget_used": 10, "budget_limit": 10}, "budget exceeded"),
        ({"active_executions": 2, "concurrency_limit": 2}, "concurrency limit"),
        ({"requested_secret": "prod", "secret_names": []}, "secret is outside"),
        ({"export_secret": True}, "non-exportable"),
    ],
)
async def test_policy_denials_block_agent_execution_before_executor(policy_context, error):
    work_item, agent = make_agent_work_item(policy_context)
    calls = []

    class Executor:
        async def dispatch(self, *_args):
            calls.append(True)
            return {"status": "success"}

    service = UnifiedExecutionService(DispatchDb(work_item, agent), agent_executor=Executor())

    with pytest.raises(ExecutionPolicyError, match=error):
        await service.dispatch(work_item)

    assert calls == []
    assert work_item.status is WorkItemStatus.ASSIGNED


@pytest.mark.asyncio
async def test_cross_tenant_agent_is_rejected_before_execution():
    work_item, agent = make_agent_work_item({})
    agent.tenant_id = uuid4()
    calls = []

    class Executor:
        async def dispatch(self, *_args):
            calls.append(True)
            return {"status": "success"}

    service = UnifiedExecutionService(DispatchDb(work_item, agent), agent_executor=Executor())

    with pytest.raises(ExecutionError, match="agent executor is unavailable"):
        await service.dispatch(work_item)

    assert calls == []
    assert work_item.status is WorkItemStatus.FAILED


@pytest.mark.asyncio
async def test_approval_full_path_blocks_then_allows_same_agent_execution():
    work_item, agent = make_agent_work_item(
        {"requires_approval": True, "approved": False, "required_capability": "run", "capabilities": ["run"]}
    )
    calls = []

    class Executor:
        async def dispatch(self, *_args):
            calls.append(True)
            return {"status": "success", "result": "approved-and-executed"}

    db = DispatchDb(work_item, agent)
    service = UnifiedExecutionService(db, agent_executor=Executor())

    waiting = await service.dispatch(work_item)

    assert waiting.waiting_for_approval is True
    assert waiting.dispatched is False
    assert calls == []
    assert work_item.status is WorkItemStatus.WAITING_APPROVAL

    work_item.policy_context["approved"] = True
    work_item.status = WorkItemStatus.ASSIGNED
    completed = await service.dispatch(work_item)

    assert completed.dispatched is True
    assert completed.waiting_for_approval is False
    assert calls == [True]
    assert work_item.status is WorkItemStatus.SUCCEEDED
    assert work_item.output_data["result"] == "approved-and-executed"
