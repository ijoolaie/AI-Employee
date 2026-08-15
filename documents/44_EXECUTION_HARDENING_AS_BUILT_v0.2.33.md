# Execution Hardening — As-Built v0.2.33

## Scope
This release hardens the v0.2.32 Workflow Engine around four execution pillars: Parallel Execution, Retry/Recovery, Global Idempotency, and Observability.

## Implemented

### 1. Parallel Execution
- Added `parallel` workflow step type.
- A parallel step contains durable branch definitions.
- Branches are persisted in `workflow_parallel_branch_runs`.
- Each branch is dispatched independently through the transactional outbox.
- Branches execute concurrently at the Celery worker boundary.
- Parent step enters `waiting_parallel` until all branches complete.
- Any failed branch fails the parent step; all successful branches are joined into one output object.
- v0.2.33 intentionally supports employee steps inside parallel branches; nested parallel/approval/condition branches are deferred.

### 2. Retry / Recovery
- Workflow step retry state is persisted in `workflow_step_runs.next_retry_at` and `attempt`.
- Retry delay uses bounded exponential backoff (`retry_backoff_seconds` metadata, default 2 seconds, capped at 300 seconds).
- Retry scheduling is durable through the outbox instead of relying only on Celery retry state.
- If a worker crashes after an Employee Run succeeds but before the Workflow Step is committed, the next execution detects the successful child Run and does not execute the employee again.
- Celery task retries remain as a secondary worker-level recovery mechanism.

### 3. Global Idempotency
- Workflow Run creation accepts `Idempotency-Key` header or request-body `idempotency_key`.
- `(tenant_id, workflow_id, idempotency_key)` is database-unique.
- Workflow Step Runs are database-unique by `(workflow_run_id, step_key)`.
- Outbox messages support a durable unique `dedupe_key`.
- Workflow execution uses a generation-based dedupe key so duplicate dispatches for the same execution generation collapse safely.
- Workflow execution acquires a row lock on the Workflow Run, preventing concurrent workers from progressing the same run simultaneously.

### 4. Observability
- Added durable Workflow Observability API:
  `GET /api/v1/workflows/{workflow_id}/runs/{run_id}/observability`
- Reports run duration, step counts/statuses, total attempts, retry count, parallel branch counts/statuses, outbox state, deadline and timestamps.
- Existing audit, AI provider call and Run Trace remain intact.

## Verification
- Python source compilation: PASS.
- New schema/model source checks: PASS by compilation.
- Full pytest: NOT VERIFIED because the delivery environment is missing `asyncpg` (and earlier full collection also required `python-jose`).
- PostgreSQL migration execution: NOT VERIFIED without a real PostgreSQL instance.
- Release ZIP is rebuilt without `__pycache__`, `.pyc`, and `.pytest_cache`.

## Explicit limitations
- Parallel branches currently support Employee steps only.
- Exactly-once external side effects are not claimed; the design is at-least-once with durable idempotency at workflow/outbox boundaries.
- Production metrics export (Prometheus/OpenTelemetry) is deferred; v0.2.33 provides durable workflow execution observability through the API.
