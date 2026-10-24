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

- `whatsapp.send_text` is registered as an external side-effecting Tool with `run.execute`, a strict input schema, and mandatory approval.
- The governed registry path requires the active Agent Run context, a consumed `ToolApprovalRequest` matching the exact tenant, Run, tool name, tool-call ID, and full arguments, plus an active WhatsApp channel owned by that tenant before creating a transactional `whatsapp.send_text` outbox row.
- The outbox dispatcher routes the row to `whatsapp_worker`. The worker rechecks the consumed approval, exact arguments, tenant/channel ownership, channel activity/type, and current Agent policy before invoking the provider-neutral `deliver_text` boundary.
- Before the provider request, the worker commits the row as `uncertain`. A crash or exception after this boundary is not automatically retried; manual reconciliation is required to avoid duplicate customer messages. The dispatcher also excludes WhatsApp rows from stale-processing redispatch.
- Direct calls to `deliver_text` remain a lower-level adapter API, not an approval gate. Production use must go through the governed Tool Registry and outbox path.
- **Validation status (2026-10-24):** exact PR head `d690df60a66f42356623446955d7a6c8d1e5c59b` passed all 28 GitHub Actions workflows, including CI, CodeQL, Runtime Isolation/RBAC, and Security/Privacy. Local focused regression tests passed (`17 passed`) for the approval policy, security regression, outbox dispatch, and WhatsApp worker. The full backend suite was not confirmed: the first root-level invocation failed during collection because a test expects the `backend` working directory, and a retry did not return a usable result. Docker Engine was unavailable locally, so DB/Docker acceptance and live provider delivery were not run. Live delivery is not certified.

## Database

One migration is required:
`9f3a1c7b2d10_tool_approval_requests.py`

Apply with Alembic before using the approval endpoints.

## v0.2.21 extension

The first real external side-effect is implemented as `send_email`. The approval infrastructure is exercised by a production-shaped external integration.

## Deferred

- Live WhatsApp provider acceptance, provider-outcome reconciliation, and end-to-end tenant/approval/runtime certification.
- Approval policies by tenant/plan/tool risk class.
- Multi-approver quorum.
- Approval expiration/timeout escalation.
- Signed approval evidence and immutable compliance archive.
