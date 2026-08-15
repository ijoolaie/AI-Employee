# Current As-Built State v0.2.33

`v0.2.33` extends the hardened `v0.2.31.1` baseline with workflow-level timeout and cooperative cancellation.

Implemented cumulative domains include tenant/RBAC, Employee Runs, AI Gateway/LM Studio, validation, RAG, memory lifecycle/extraction, tool approval, durable SMTP/outbox dispatch, workflow conditions/schedules/events, human approval/wait-resume, and workflow timeout/cancellation.

Not yet implemented as generalized workflow orchestration features: parallel branches, compensation/replay, forced process termination, and visual workflow builder.

Full integration verification is not claimed unless PostgreSQL, Redis/Celery, and all runtime dependencies are available.


## v0.2.33 execution hardening

- Parallel workflow branches are durable and dispatched independently through the outbox.
- Workflow step retry state is persisted with bounded exponential backoff.
- Workflow Run creation supports Idempotency-Key.
- Workflow Step Runs and Outbox dispatches have database-backed deduplication safeguards.
- Workflow execution uses a row lock to prevent concurrent progression of the same run.
- Durable workflow observability is available through `/api/v1/workflows/{workflow_id}/runs/{run_id}/observability`.
- Full PostgreSQL migration and full pytest remain NOT VERIFIED in the current delivery environment.
