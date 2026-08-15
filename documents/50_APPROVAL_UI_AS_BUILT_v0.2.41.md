# Approval UI — As-Built v0.2.41

## Scope
Unified the customer Approval Center for Tool Approvals and durable Workflow Approvals.

## Tool approvals
- Lists pending tool approvals from `/api/v1/approvals`.
- Shows tool name, run, request time and arguments.
- Approve/Reject with optional reason.
- Approval decisions invalidate run/approval queries.

## Workflow approvals
- Lists pending workflow approvals from `/api/v1/workflow-approvals`.
- Shows step key, workflow run, creation time, expiry and metadata.
- Approve resumes the durable workflow through the existing backend endpoint.
- Reject marks the workflow step/run failed through the existing durable workflow approval path.
- Decision reasons are capped at the backend contract limit (2000 characters).

## Security
The UI does not bypass authorization. Tenant isolation and RBAC remain enforced by the backend contexts on both approval APIs.

## Verification
- TypeScript source inspected for API/type alignment.
- Backend approval endpoints inspected for tenant scope, row locking, expiration and audit behavior.
- Frontend build is not claimed in an environment without installed `node_modules`.
- PostgreSQL/Redis/Celery E2E remains separately pending.
