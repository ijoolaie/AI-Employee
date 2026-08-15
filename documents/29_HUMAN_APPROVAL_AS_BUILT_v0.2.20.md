# Human Approval / Tool Execution Policy — As-Built v0.2.20

## Implemented

- Durable `tool_approval_requests` table with tenant/run/tool scoping.
- Tool approval lifecycle: `pending -> approved -> consumed` or `pending -> rejected`.
- Run status `waiting` when a Tool requires human approval.
- Worker pauses a Run instead of executing a gated Tool.
- Approval stores the validated Tool arguments and serialized continuation messages so execution can resume deterministically from the approval boundary.
- Approval decision is protected by tenant-scoped RBAC permissions:
  - `approval.read`
  - `approval.decide`
- Approval decision uses row locks and rejects double decisions.
- Approve requeues the Run through the existing Celery execution path.
- Reject marks the Run failed with a structured `TOOL_APPROVAL_REJECTED` error.
- Approval requests and decisions are written to Audit Log.
- Frontend `/approvals` page provides pending approval review and approve/reject actions.
- Run detail page exposes the `waiting` state and directs the user to Approvals.

## Security invariants

A model ToolCall never grants itself permission. A gated Tool must still be registered, allowed by the immutable EmployeeVersion, pass JSON Schema validation, satisfy worker-side RBAC, and have a recorded human approval before execution.

## Current production tools

The registry now also ships `send_email`, the first side-effecting external Tool. It requires `run.execute` and `requires_approval=True`; SMTP execution occurs only after explicit approval and resumes through Celery.

## Database

One migration is required:
`9f3a1c7b2d10_tool_approval_requests.py`

Apply with Alembic before using the approval endpoints.

## v0.2.21 extension

The first real external side-effect is implemented as `send_email`. The approval infrastructure is now exercised by a production-shaped external integration.

## Deferred

- Real external side-effecting tools.
- Approval policies by tenant/plan/tool risk class.
- Multi-approver quorum.
- Approval expiration/timeout escalation.
- Signed approval evidence and immutable compliance archive.
