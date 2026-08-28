from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.unified_execution import ExecutionError, UnifiedExecutionService


def item(*, executor_type=ExecutorType.HUMAN, requires_approval=False):
    return SimpleNamespace(
        id=uuid4(), tenant_id=uuid4(), title="Parent", description="context",
        status=WorkItemStatus.RUNNING, priority=1, requester_id=uuid4(),
        executor_type=executor_type, executor_id=uuid4(), input_data={"source": "parent"},
        output_data={}, policy_context={"requires_approval": requires_approval},
    )


def test_phase84_delegation_preserves_tenant_parent_and_context():
    parent = item()
    service = UnifiedExecutionService(SimpleNamespace())
    target = uuid4()

    child = service.delegate(
        parent, actor_id=parent.executor_id, target_type=ExecutorType.AGENT,
        target_id=target, context={"customer": "acme"},
        artifacts=[{"id": "doc-1", "kind": "quote"}],
    )

    assert child.tenant_id == parent.tenant_id
    assert child.parent_work_item_id == parent.id
    assert child.executor_type is ExecutorType.AGENT
    assert child.executor_id == target
    assert child.status is WorkItemStatus.ASSIGNED
    assert child.input_data["delegated_context"] == {"customer": "acme"}
    assert child.input_data["delegated_artifacts"][0]["id"] == "doc-1"


def test_phase84_delegation_requires_current_executor():
    parent = item()
    service = UnifiedExecutionService(SimpleNamespace())
    with pytest.raises(ExecutionError, match="not authorized"):
        service.delegate(
            parent, actor_id=uuid4(), target_type=ExecutorType.AGENT, target_id=uuid4()
        )


def test_phase84_approval_gated_delegation_waits_before_target_execution():
    parent = item(requires_approval=True)
    service = UnifiedExecutionService(SimpleNamespace())
    child = service.delegate(
        parent, actor_id=parent.executor_id, target_type=ExecutorType.HUMAN, target_id=uuid4()
    )
    assert child.status is WorkItemStatus.WAITING_APPROVAL
    assert child.policy_context["requires_approval"] is True
