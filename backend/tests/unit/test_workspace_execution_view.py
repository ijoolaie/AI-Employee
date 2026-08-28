from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.work_item import ExecutorType, WorkItemStatus
from app.services.workspace_execution_view import WorkspaceExecutionView


def test_workspace_view_exposes_lifecycle_policy_and_delegation():
    tenant = uuid4()
    parent = uuid4()
    item = SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant,
        status=WorkItemStatus.WAITING_APPROVAL,
        executor_type=ExecutorType.HUMAN,
        executor_id=uuid4(),
        parent_work_item_id=parent,
        output_data=None,
        policy_context={
            "requires_approval": True,
            "approved": False,
            "handoff_target_agent_id": "agent-2",
            "api_secret": "hidden",
        },
    )

    view = WorkspaceExecutionView.from_work_item(item, actor_tenant_id=tenant)

    assert view["status"] == WorkItemStatus.WAITING_APPROVAL.value
    assert view["approval_required"] is True
    assert view["delegation"]["parent_work_item_id"] == str(parent)
    assert "api_secret" not in view["policy"]


def test_workspace_view_rejects_cross_tenant_access():
    item = SimpleNamespace(
        id=uuid4(),
        tenant_id=uuid4(),
        status=WorkItemStatus.READY,
        executor_type=ExecutorType.AGENT,
        executor_id=uuid4(),
        parent_work_item_id=None,
        output_data=None,
        policy_context={},
    )

    with pytest.raises(PermissionError, match="tenant mismatch"):
        WorkspaceExecutionView.from_work_item(item, actor_tenant_id=uuid4())
