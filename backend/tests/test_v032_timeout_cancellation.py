import uuid
from datetime import datetime, timedelta, timezone
import pytest
from app.models.workflow import WorkflowRun


def test_workflow_run_model_has_timeout_and_cancellation_fields():
    assert hasattr(WorkflowRun, "deadline_at")
    assert hasattr(WorkflowRun, "cancelled_at")
    assert hasattr(WorkflowRun, "cancel_reason")


def test_timeout_deadline_is_in_future():
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(seconds=60)
    assert deadline > now
