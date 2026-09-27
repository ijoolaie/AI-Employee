from __future__ import annotations

import uuid
import pytest

from app.models.run import Run
from app.models.work_item import ExecutorType, WorkItem, WorkItemStatus
from app.services.run_service import _sync_work_item_lifecycle


class _Result:
    def __init__(self, scalar=None, rows=None):
        self.scalar = scalar
        self.rows = rows or []

    def scalar_one_or_none(self):
        return self.scalar

    def scalars(self):
        return self

    def all(self):
        return self.rows


class _DB:
    def __init__(self, child, parent, children):
        self.results = [_Result(scalar=child), _Result(scalar=parent), _Result(rows=children)]

    async def execute(self, _statement):
        return self.results.pop(0)


def _item(tenant_id, *, status, parent_id=None, policy_context=None):
    return WorkItem(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        title="item",
        status=status,
        priority=0,
        executor_type=ExecutorType.AGENT,
        executor_id=uuid.uuid4(),
        input_data={},
        output_data={},
        policy_context=policy_context or {},
        idempotency_key=str(uuid.uuid4()),
        parent_work_item_id=parent_id,
    )


@pytest.mark.asyncio
async def test_run_success_completes_child_and_team_parent():
    tenant_id = uuid.uuid4()
    parent = _item(tenant_id, status=WorkItemStatus.RUNNING, policy_context={"member_count": 2})
    child = _item(tenant_id, status=WorkItemStatus.RUNNING, parent_id=parent.id)
    sibling = _item(tenant_id, status=WorkItemStatus.SUCCEEDED, parent_id=parent.id)
    run = Run(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        employee_id=uuid.uuid4(),
        employee_version_id=uuid.uuid4(),
        work_item_id=child.id,
        status="success",
        input_data={},
    )

    await _sync_work_item_lifecycle(_DB(child, parent, [child, sibling]), run=run, status="success")

    assert child.status is WorkItemStatus.SUCCEEDED
    assert parent.status is WorkItemStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_run_failure_fails_child_and_team_parent():
    tenant_id = uuid.uuid4()
    parent = _item(tenant_id, status=WorkItemStatus.RUNNING, policy_context={"member_count": 2})
    child = _item(tenant_id, status=WorkItemStatus.RUNNING, parent_id=parent.id)
    sibling = _item(tenant_id, status=WorkItemStatus.RUNNING, parent_id=parent.id)
    run = Run(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        employee_id=uuid.uuid4(),
        employee_version_id=uuid.uuid4(),
        work_item_id=child.id,
        status="failed",
        input_data={},
    )

    await _sync_work_item_lifecycle(_DB(child, parent, [child, sibling]), run=run, status="failed", error="provider failed")

    assert child.status is WorkItemStatus.FAILED
    assert child.output_data["run_error"] == "provider failed"
    assert parent.status is WorkItemStatus.FAILED


@pytest.mark.asyncio
async def test_run_waiting_for_approval_blocks_team_parent_until_resume():
    tenant_id = uuid.uuid4()
    parent = _item(tenant_id, status=WorkItemStatus.RUNNING, policy_context={"member_count": 2})
    child = _item(tenant_id, status=WorkItemStatus.RUNNING, parent_id=parent.id)
    sibling = _item(tenant_id, status=WorkItemStatus.SUCCEEDED, parent_id=parent.id)
    run = Run(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        employee_id=uuid.uuid4(),
        employee_version_id=uuid.uuid4(),
        work_item_id=child.id,
        status="waiting",
        input_data={},
    )

    await _sync_work_item_lifecycle(_DB(child, parent, [child, sibling]), run=run, status="waiting")

    assert child.status is WorkItemStatus.WAITING_APPROVAL
    assert parent.status is WorkItemStatus.WAITING_APPROVAL



@pytest.mark.asyncio
async def test_late_run_completion_does_not_resurrect_cancelled_child():
    tenant_id = uuid.uuid4()
    child = _item(tenant_id, status=WorkItemStatus.CANCELLED)
    run = Run(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        employee_id=uuid.uuid4(),
        employee_version_id=uuid.uuid4(),
        work_item_id=child.id,
        status="success",
        input_data={},
    )

    await _sync_work_item_lifecycle(_DB(child, None, []), run=run, status="success")

    assert child.status is WorkItemStatus.CANCELLED


@pytest.mark.asyncio
async def test_late_child_completion_does_not_resurrect_cancelled_team_parent():
    tenant_id = uuid.uuid4()
    parent = _item(tenant_id, status=WorkItemStatus.CANCELLED, policy_context={"member_count": 1})
    child = _item(tenant_id, status=WorkItemStatus.RUNNING, parent_id=parent.id)
    run = Run(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        employee_id=uuid.uuid4(),
        employee_version_id=uuid.uuid4(),
        work_item_id=child.id,
        status="success",
        input_data={},
    )

    await _sync_work_item_lifecycle(_DB(child, parent, []), run=run, status="success")

    assert child.status is WorkItemStatus.SUCCEEDED
    assert parent.status is WorkItemStatus.CANCELLED
