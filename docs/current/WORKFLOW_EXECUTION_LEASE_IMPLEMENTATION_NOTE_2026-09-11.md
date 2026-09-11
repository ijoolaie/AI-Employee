# Implementation Note — Workflow Execution Lease

This branch establishes the durable lease schema and regression contract for WorkflowRun recovery. The service integration must atomically acquire ownership, verify ownership before every side-effect boundary, heartbeat while executing, and recover only expired leases. No status-only retry is permitted.
