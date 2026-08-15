# As-Built Current State v0.2.21

## Implemented

- All v0.2.20 capabilities.
- First side-effecting external Tool: `send_email` via configured SMTP.
- Durable Human Approval workflow for gated Tool calls.
- `waiting` Run state.
- Approval request persistence with Tool arguments and continuation context.
- `approval.read` and `approval.decide` permissions.
- Worker-side resume after approval.
- Rejection path with structured Run failure.
- Approval audit events.
- Frontend Approvals page.

## Current tools

- `calculator`: `run.execute`, no approval, no side effects.
- `current_time`: `run.execute`, no approval, no side effects.
- `send_email`: `run.execute`, side-effecting, always requires Human Approval, fail-closed recipient-domain allowlist.

## Next capability boundary

The first external side-effect boundary is now shipped. Next capabilities are RAG/Memory or additional narrowly scoped external adapters, plus tool-specific quotas/billing and advanced approval policies.

## Still pending

- Additional external Tool adapters.
- Tool-specific billing/cost policy.
- RAG.
- Memory.
- Workflow Engine.
- Quotas/Billing.
- Approval expiration, escalation and multi-approver policies.
