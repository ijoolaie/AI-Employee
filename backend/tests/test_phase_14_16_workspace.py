from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from app.api.v1.workspace import WorkspaceWorkItem, _approval


def test_workspace_work_item_exposes_unified_executor_fields():
    item = SimpleNamespace(
        id=uuid4(),
        title="Review contract",
        status=SimpleNamespace(value="ready"),
        priority=10,
        executor_type=SimpleNamespace(value="human"),
        executor_id=uuid4(),
        requester_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    view = WorkspaceWorkItem(item)
    assert view.title == "Review contract"
    assert view.status == "ready"
    assert view.executor_type == "human"


def test_workspace_approval_normalizes_workflow_and_tool_shapes():
    approval = SimpleNamespace(
        id=uuid4(),
        status="pending",
        requested_by=uuid4(),
        decided_by=None,
        decision_reason=None,
        created_at=datetime.now(timezone.utc),
        decided_at=None,
        metadata_={"step_key": "approval"},
    )
    view = _approval(approval, "workflow")
    assert view["kind"] == "workflow"
    assert view["status"] == "pending"
    assert view["metadata"] == {"step_key": "approval"}
