# As-Built Current State v0.2.20

## Implemented

- All v0.2.19 capabilities.
- Durable Human Approval workflow for gated Tool calls.
- `waiting` Run state.
- Approval request persistence with Tool arguments and continuation context.
- `approval.read` and `approval.decide` permissions.
- Worker-side resume after approval.
- Rejection path with structured Run failure.
- Approval audit events.
- Frontend Approvals page.

## Current safe tools

- `calculator`: `run.execute`, no approval, no side effects.
- `current_time`: `run.execute`, no approval, no side effects.

## Next capability boundary

The architecture is now ready for the first real side-effecting/external Tool, because authorization and Human Approval are separate enforced boundaries rather than UI-only conventions.

## Still pending

- External Tool adapters.
- Side-effecting production Tools.
- Tool-specific billing/cost policy.
- RAG.
- Memory.
- Workflow Engine.
- Quotas/Billing.
- Approval expiration, escalation and multi-approver policies.
