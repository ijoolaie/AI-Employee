# As-Built Baseline v0.2.20 — LM Studio

This is the current baseline after Human-in-the-loop Tool Approval infrastructure.

## Shipped behavior

Auth/JWT, tenant isolation, RBAC, Employees/versioning, Runs, async PostgreSQL, Celery/Redis, AI Gateway, LM Studio/Gemma 4 E4B, Prompt/Context Assembly, JSON Schema validation, Audit Log, Run Trace, Usage/Cost reporting, controlled Tool Registry, bounded tool loop, worker-side Tool authorization, and durable Human Approval for gated Tool calls.

## Tool security boundary

A Tool must be registered and explicitly allowed by the immutable EmployeeVersion. Its arguments are validated against JSON Schema. The worker re-checks the Run creator's tenant-scoped permissions. If `requires_approval=True`, execution pauses the Run in `waiting`, creates a durable approval request, and does not execute the Tool until a user with `approval.decide` explicitly approves it. Approval decisions are audited and approved requests are resumed through Celery.

## Current built-ins

- `calculator`: side-effect-free, requires `run.execute`, no approval.
- `current_time`: side-effect-free, requires `run.execute`, no approval.

## Database change

Added `tool_approval_requests` through Alembic revision `9f3a1c7b2d10`.

## Still not shipped

External/browser/filesystem/database mutation Tools, RAG, Memory, Workflow Engine, Quotas, Billing, multi-approver policies, approval expiration/escalation, and external integrations.
