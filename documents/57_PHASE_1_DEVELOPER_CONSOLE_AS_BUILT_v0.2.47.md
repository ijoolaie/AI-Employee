# Phase 1 Developer Console — As Built v0.2.47

## Scope
The Phase 1 Developer Tools surface is now available inside the tenant Customer Panel. It is read-oriented and reuses existing durable Core data rather than introducing a parallel observability store.

## Delivered
- `/developer` Developer Console route.
- Tenant-scoped operational metrics: workflow runs, workflow steps, outbox pending/processing/dead.
- Recent audit-log inspection with request correlation IDs.
- Recent Run list with status, token and cost visibility.
- Direct links to existing Run Trace pages.
- Dead-letter inspection and replay through the existing durable outbox API.
- Automatic refresh for operational views.

## Backend
- `GET /api/v1/operations/audit-logs` added with `AuditReadContext` tenant isolation.
- Existing `/operations/metrics` and `/operations/dead-letters` are consumed directly.

## Security
- Audit and operational data remain tenant-scoped.
- Audit logs are read-only from the console.
- Dead-letter replay continues to require the existing workflow execution permission.

## Verification
- Python compilation/static import checks: PASS.
- Full backend pytest suite: 83 passed before this incremental release; Developer Console contract tests added for this release.
- Frontend production build remains environment-dependent when `node_modules` is unavailable.
- Real PostgreSQL/Redis/Celery/LM Studio E2E remains a separate runtime verification boundary.
