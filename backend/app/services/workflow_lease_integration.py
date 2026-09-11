"""Integration shim for workflow lease fencing.

The execution service imports these helpers so the lease boundary stays explicit
and independently testable while preserving the existing workflow state machine.
"""
from app.services.workflow_execution_lease import (
    acquire_workflow_execution_lease,
    assert_workflow_execution_lease,
    heartbeat_workflow_execution_lease,
    recover_workflow_execution_lease,
)

__all__ = [
    "acquire_workflow_execution_lease",
    "assert_workflow_execution_lease",
    "heartbeat_workflow_execution_lease",
    "recover_workflow_execution_lease",
]
