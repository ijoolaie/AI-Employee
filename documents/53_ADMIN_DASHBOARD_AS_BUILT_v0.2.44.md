# Admin Dashboard — As Built v0.2.44

## Scope
Phase 1 platform-level Admin Dashboard, separate from tenant Admin/RBAC.

## Security boundary
A new `users.is_platform_admin` flag separates platform administration from the existing tenant `is_superuser` compatibility path. Tenant administrators are **not** automatically platform administrators.

Admin API endpoints require `is_platform_admin=true`:
- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/tenants`

An explicit operator script is provided at `backend/scripts/promote_platform_admin.py`.

## Dashboard
The platform dashboard reports:
- tenant and active-tenant counts
- user count
- workflow and workflow-run counts
- AI provider call count
- total token usage
- total recorded AI cost
- failed workflow runs
- pending/dead outbox counts
- per-tenant usage/cost breakdown
- provider/model operational usage
- PostgreSQL, Redis, Celery worker, and configured AI provider health probes

Tenant aggregation uses correlated SQL subqueries to avoid cross-join multiplication of costs/counts.

## UI
New routes:
- `/admin` — platform overview
- `/admin/tenants` — tenant inventory

A dedicated dark Admin Sidebar separates platform administration from the Customer Panel. Platform Admin is shown in the Customer Sidebar only when the authenticated user has `is_platform_admin=true`.

## Explicit limitations
- Subscription/Billing entities are not fabricated because no subscription model exists in the current Phase 1 schema. The dashboard reports recorded usage/cost only.
- Platform admin promotion is an explicit operator action; no tenant registration path grants platform privileges.
- Frontend production build remains NOT VERIFIED when `node_modules` is unavailable.
- Real PostgreSQL/Redis/Celery/LM Studio E2E remains environment-dependent and must be verified separately.
