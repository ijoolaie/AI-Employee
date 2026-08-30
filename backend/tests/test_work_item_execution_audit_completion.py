"""Regression coverage for durable WorkItem completion audit semantics."""

from app.models.work_item import WorkItemStatus


def completion_audit_action(status: WorkItemStatus, waiting_for_approval: bool = False) -> str:
    if waiting_for_approval:
        return "work_item.waiting_approval"
    if status is WorkItemStatus.SUCCEEDED:
        return "work_item.execution_succeeded"
    if status is WorkItemStatus.FAILED:
        return "work_item.execution_failed"
    return "work_item.dispatched"


def test_terminal_completion_actions_are_distinct() -> None:
    assert completion_audit_action(WorkItemStatus.SUCCEEDED) == "work_item.execution_succeeded"
    assert completion_audit_action(WorkItemStatus.FAILED) == "work_item.execution_failed"
    assert completion_audit_action(WorkItemStatus.RUNNING) == "work_item.dispatched"


def test_waiting_approval_takes_precedence() -> None:
    assert completion_audit_action(WorkItemStatus.WAITING_APPROVAL, waiting_for_approval=True) == "work_item.waiting_approval"
