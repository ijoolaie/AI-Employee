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

The registry ships `send_email`, a side-effecting external Tool. It requires `run.execute` and `requires_approval=True`; SMTP execution occurs only after explicit approval and resumes through Celery.

## WhatsApp outbound status (2026-10-23)

- The provider adapter and provider-neutral `deliver_text` boundary exist.
- The central mandatory approval policy now reserves `whatsapp.send_text` as approval-required, even if a future registration omits its local flag.
- **Not yet implemented:** a registry-backed `whatsapp.send_text` Tool wired to durable approval context. The adapter must not be treated as an approved production sending path until that integration and its end-to-end tests are delivered. This policy entry alone does not gate direct calls to `deliver_text`.

## Database

One migration is required:
`9f3a1c7b2d10_tool_approval_requests.py`

Apply with Alembic before using the approval endpoints.

## v0.2.21 extension

The first real external side-effect is implemented as `send_email`. The approval infrastructure is exercised by a production-shaped external integration.

## Deferred

- Registry-backed WhatsApp outbound delivery with durable approval and exact-call binding.
- Approval policies by tenant/plan/tool risk class.
- Multi-approver quorum.
- Approval expiration/timeout escalation.
- Signed approval evidence and immutable compliance archive.
