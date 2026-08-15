# Workflow Engine Foundation — As-Built v0.2.28

## Scope

v0.2.28 introduces the first production-oriented Workflow Engine foundation. It intentionally implements the smallest useful slice of the long-term Workflow Engine design: versioned, tenant-scoped, manually triggered, linear workflows whose primary Action is an Employee Run.

## Implemented

- Tenant-scoped `Workflow` identity with unique slug.
- Immutable `WorkflowVersion` records; executions lock to the selected version.
- Manual Workflow Run creation.
- Durable `WorkflowRun` state: `pending → running → success | failed`.
- Durable `WorkflowStepRun` records with position, status, attempt, input/output and linked Employee Run.
- Employee Action steps.
- Context propagation between steps.
- Explicit input mapping using `$.input.*` and `$.steps.<key>.*` references.
- Step-level retry count (`retry_max`, bounded 0–5).
- Child Employee Runs retain their own version, trace, AI usage and cost records.
- Workflow-level audit events.
- Tenant RBAC permissions: `workflow.read`, `workflow.write`, `workflow.execute`.
- Celery worker execution using the existing Windows-safe `worker_db_session` pattern.

## Deliberate v0.2.28 limits

The following are not claimed as implemented:

- Schedule/Celery Beat trigger
- Event triggers
- API/webhook triggers beyond the manual Run endpoint
- Condition steps
- Loop steps
- Wait/Approval steps as first-class Workflow steps
- Compensation/replay
- Parallel execution
- Workflow cancellation
- Step timeout enforcement
- Visual Workflow Builder

These remain future Workflow Engine increments.

## Runtime path

`POST /workflows/{id}/runs` → durable WorkflowRun → Celery → resolve locked WorkflowVersion → execute ordered Employee Action steps → create and execute child Employee Runs → propagate outputs into Workflow context → complete WorkflowRun.

## Verification

- Python source compilation: PASS.
- Workflow schema/static validation tests: PASS.
- ZIP integrity: PASS.
- Real `.env`: excluded.
- `__pycache__` / `.pyc`: excluded.
- Full pytest remains environment-dependent when `asyncpg` / `python-jose` are absent; this is never reported as a false PASS.
