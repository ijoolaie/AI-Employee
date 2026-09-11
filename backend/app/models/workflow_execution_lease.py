"""Shared constants for durable WorkflowRun execution ownership."""
from datetime import timedelta

WORKFLOW_EXECUTION_LEASE_SECONDS = 120
WORKFLOW_EXECUTION_HEARTBEAT_SECONDS = 20
WORKFLOW_EXECUTION_LEASE_DURATION = timedelta(seconds=WORKFLOW_EXECUTION_LEASE_SECONDS)
