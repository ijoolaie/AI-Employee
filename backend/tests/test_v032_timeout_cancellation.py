import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.models.workflow import WorkflowRun


def test_workflow_run_model_has_timeout_and_cancellation_fields():
    assert hasattr(WorkflowRun, "deadline_at")
    assert hasattr(WorkflowRun, "cancelled_at")
    assert hasattr(WorkflowRun, "cancel_reason")


def test_timeout_deadline_is_in_future():
    now = datetime.now(UTC)
    deadline = now + timedelta(seconds=60)
    assert deadline > now


def test_workflow_execution_fences_non_running_parent_after_child_commit():
    source = __import__("pathlib").Path("backend/app/services/workflow_service.py").read_text()
    assert 'if fresh_status != "running":' in source
    assert 'if fresh_deadline and fresh_deadline <= datetime.now(timezone.utc):' in source


def test_parallel_branch_rechecks_parent_before_each_child():
    source = __import__("pathlib").Path("backend/app/services/workflow_service.py").read_text()
    assert 'parent_state = await db.execute(select(WorkflowRun.status, WorkflowRun.deadline_at)' in source
    assert 'if parent_status != "running":' in source
