# Customer Dashboard — As Built v0.2.45

## Status
Phase 1 Customer Dashboard completed on top of v0.2.44.

## Tenant-scoped dashboard
Added `GET /api/v1/customer-dashboard` using the authenticated tenant context.

The endpoint aggregates:
- employee inventory and active employees
- workflow inventory and active workflows
- workflow run volume, running/success/failed counts
- pending workflow approvals
- active schedules
- active webhook triggers
- AI provider calls, success/failure, tokens, cost and latency
- recent workflow runs with AI-provider cost attribution

## Frontend
`/dashboard` now provides:
- operational KPI cards
- workflow success/failure visibility
- recent workflow runs
- AI health/usage summary
- pending approval, schedule and webhook shortcuts
- automatic 15-second refresh

## Security
All dashboard data is resolved from the authenticated tenant context. The dashboard endpoint has no tenant-id query parameter and does not permit cross-tenant selection.

## Verification
- Python AST / compile: PASS
- Targeted Phase 1 regression tests: 14/14 PASS
- Alembic graph: existing single-head chain retained
- Frontend production build: NOT VERIFIED because `node_modules` is not present in the build environment
- PostgreSQL/Redis/Celery/LM Studio E2E: NOT VERIFIED until real services are available
