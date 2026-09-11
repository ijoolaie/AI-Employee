"""Shared constants for durable WorkflowRun execution ownership."""
from datetime import timedelta

# The lease is intentionally longer than the periodic recovery sweep. Normal
# execution renews it at workflow step boundaries; recovery is only eligible
# after this bounded ownership window expires.
WORKFLOW_EXECUTION_LEASE_SECONDS = 300
WORKFLOW_EXECUTION_HEARTBEAT_SECONDS = 20
WORKFLOW_EXECUTION_LEASE_DURATION = timedelta(seconds=WORKFLOW_EXECUTION_LEASE_SECONDS)
