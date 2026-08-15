# Workflow Timeout & Cancellation — As Built v0.2.32

Baseline: `v0.2.31.1`.

## Implemented

- Optional workflow-level `max_runtime_seconds` configuration.
- Durable `WorkflowRun.deadline_at` persisted with the run.
- Cooperative cancellation through `POST /api/v1/workflows/{workflow_id}/runs/{run_id}/cancel`.
- New RBAC permission: `workflow.cancel`.
- Cancellation metadata: `cancelled_at` and `cancel_reason`.
- Terminal workflow status `cancelled`.
- Terminal workflow status `timed_out`.
- Worker-side timeout and cancellation checks before advancing each workflow step.
- Periodic timeout sweep through Celery Beat for runs that remain pending/running/waiting beyond their deadline.
- Audit events for cancellation and timeout.
- Existing durable outbox architecture remains unchanged.

## Semantics

Cancellation is cooperative. It prevents further workflow advancement; it does not forcibly terminate an already-running external Employee/AI process.

Timeout is also cooperative at the workflow orchestration boundary. The timeout sweep marks overdue runs terminal and prevents subsequent workflow advancement.

## Verification

- Python compilation: PASS when executed in the build environment.
- Static model/schema coverage added.
- Full PostgreSQL/Celery integration remains subject to the project's runtime verification environment.
