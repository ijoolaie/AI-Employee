from types import SimpleNamespace
import uuid

import pytest

from app.services import workflow_service


class _FakeScalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _FakeResult:
    def __init__(self, *rows):
        self._rows = rows

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def scalars(self):
        return _FakeScalars(self._rows)


class _FakeDb:
    def __init__(self, results):
        self._results = iter(results)
        self.executed = []

    async def execute(self, statement):
        self.executed.append(statement)
        return next(self._results)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_cancel_workflow_run_cancels_queued_children_and_branches_but_not_running_run(monkeypatch):
    tenant_id = uuid.uuid4()
    workflow_run_id = uuid.uuid4()
    step_run_id = uuid.uuid4()
    branch_run_id = uuid.uuid4()

    workflow_run = SimpleNamespace(
        id=workflow_run_id,
        tenant_id=tenant_id,
        status="running",
        cancelled_at=None,
        cancel_reason=None,
        completed_at=None,
        error=None,
    )
    pending_step_child = SimpleNamespace(
        status="pending",
        error_message=None,
        completed_at=None,
    )
    waiting_branch_child = SimpleNamespace(
        status="waiting",
        error_message=None,
        completed_at=None,
    )
    running_child = SimpleNamespace(
        status="running",
        error_message=None,
        completed_at=None,
    )
    branch = SimpleNamespace(
        status="running",
        completed_at=None,
        execution_lease_id=uuid.uuid4(),
        execution_lease_expires_at=object(),
        execution_heartbeat_at=object(),
    )

    db = _FakeDb(
        [
            _FakeResult(workflow_run),
            _FakeResult(step_run_id),
            _FakeResult(branch_run_id),
            _FakeResult(pending_step_child, waiting_branch_child),
            _FakeResult(branch),
        ]
    )

    async def record_audit(*args, **kwargs):
        return None

    monkeypatch.setattr(workflow_service.audit_service, "record", record_audit)

    result = await workflow_service.cancel_workflow_run(
        db,
        workflow_run_id=workflow_run_id,
        tenant_id=tenant_id,
        cancelled_by=uuid.uuid4(),
        reason="operator requested cancellation",
    )

    assert result is workflow_run
    assert workflow_run.status == "cancelled"
    assert workflow_run.cancel_reason == "operator requested cancellation"
    assert workflow_run.error["code"] == "WORKFLOW_CANCELLED"

    assert pending_step_child.status == "cancelled"
    assert waiting_branch_child.status == "cancelled"
    assert pending_step_child.error_message == (
        "Run cancelled because its WorkflowRun was cancelled"
    )
    assert waiting_branch_child.error_message == (
        "Run cancelled because its WorkflowRun was cancelled"
    )

    assert running_child.status == "running"
    assert running_child.completed_at is None

    assert branch.status == "cancelled"
    assert branch.execution_lease_id is None
    assert branch.execution_lease_expires_at is None
    assert branch.execution_heartbeat_at is None
    assert len(db.executed) == 5


@pytest.mark.asyncio
async def test_parent_execution_fence_returns_terminal_cancellation_without_raising():
    workflow_run = SimpleNamespace(status="cancelled")
    db = _FakeDb([_FakeResult(workflow_run)])

    result = await workflow_service._lock_parent_for_child_execution(
        db,
        workflow_run_id=uuid.uuid4(),
    )

    assert result is workflow_run
    assert result.status == "cancelled"
