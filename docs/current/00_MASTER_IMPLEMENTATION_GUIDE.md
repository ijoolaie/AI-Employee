# AI Employee Platform — Master Implementation & Delivery Guide

**Last hand-off reconciliation:** 2026-10-09  
**Latest published and exact-SHA certified release:** `v1.4.17`  
**Certified release SHA:** `b403c0dcdea579e017738a6fdea138c2b1a2999c`  
**Mutable engineering baseline at last verified checkpoint:** `7adeacfeca998df9af78be157bb032a9ea0a8dd8`  
**Release boundary:** engineering commits on `main` are not release-certified unless a new exact-SHA certification and release promotion explicitly says so.

This is the repository's master implementation and hand-off guide. For the current release/certification truth, defer to `docs/00_START_HERE/CURRENT_STATUS.md`; for near-term priorities, use `docs/00_START_HERE/CURRENT_PRIORITIES.md`. Resolve the live `main` SHA from Git metadata before starting work; the SHA above is a dated snapshot, not a claim that it remains the live head.


## Current engineering hand-off — 2026-10-09

### Completed repository hygiene
- Dependency PR triage completed: no open PRs remained at the 2026-10-08 checkpoint. Four compatible updates were merged; three incompatible/conflicted PRs were closed with reasons recorded in their discussions.
- At the 2026-10-09 engineering checkpoint `12c93e6809a659e0ee8251385a101fb1b309094a`, all 10 reported check runs completed successfully. F8 PR #977 subsequently passed CI (frontend/backend), CodeQL (JavaScript/TypeScript and Python), DAST, infrastructure validation, and HA recovery validation on head `6b56f403f0e4daa4e191e226999ba0b15a0af7ad`, then merged as `7adeacfeca998df9af78be157bb032a9ea0a8dd8`. This is engineering CI evidence only, not production certification.
- Issue [#975](https://github.com/ijoolaie/AI-Employee/issues/975) tracks the missing `main` branch protection/ruleset. Protection was not enabled by the connected integration; a repository owner/admin must configure it and verify the required PR check contexts.

### AI Company World — next product slice
- F0–F7 are engineering implementation; the renderer remains Canvas. PixiJS is not installed and must not be claimed as validated.
- The office endpoint `GET /api/v1/customer-dashboard/office` is tenant-scoped and read-only. Its current employee contract has identity, kind, activity/presentation state, latest run, and current work item, but **no authoritative department/team/location assignment**.
- Do not infer department from employee name, slug, `kind`, role, work item, run, or array order. World department zones are presentation-only.
- F8 first slice merged in [PR #977](https://github.com/ijoolaie/AI-Employee/pull/977): stable unique presentation slots are derived from sorted employee IDs, independent of API response order, and the projected `departmentId` is explicitly `null` until an authoritative tenant-scoped assignment exists. This does not create backend organizational truth. Any later domain-owned assignment field/API is a separate decision requiring a justified source model, migration/API contract, and tenant-isolation tests.
- Required validation for the F8 change: World unit/contract tests, lint/typecheck/build, Playwright World smoke, tenant-isolation tests if the backend contract changes, and confirm Management Mode is unchanged. No local runtime execution is claimed from this GitHub-only hand-off.
- No new production certification is implied. `v1.4.17` certification remains bound only to `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

### Next actions
1. Decide explicitly whether a real domain-owned employee department assignment is justified. Until a source of truth exists, keep `departmentId = null` and visual placement presentation-only.
2. Complete Issue #975 with an owner/admin enabling and verifying branch protection.
3. Reconcile current-priority/status docs using dated checkpoints instead of repeatedly hard-coding a mutable `main` SHA.
4. Resolve the live `main` SHA from Git metadata before the next implementation; this hand-off SHA is a dated checkpoint.

## Release and productization topology

The platform is being prepared for three distinct delivery levels:

- **Vendor Edition:** primary seller control plane, licensing, global configuration, release authority, and support operations.
- **Reseller Edition:** delegated commercial administration and customer provisioning within a bounded tenant/control plane.
- **Customer Edition:** isolated customer operations, configuration, data, recovery, and upgrade surface.

See `docs/current/PRODUCTIZATION_ROADMAP.md` for the phase-by-phase delivery plan.

## Current release integrity

- Published release: `v1.0.1`.
- Published release commit: `2d23a01098f432145ecaea14b2500fe520ad0bf7`.
- Current `main` is intentionally separate from the published release when it contains post-release changes.
- Certification evidence from RC8/RC9 and production hardening remains valid unless a later change affects the relevant behavior.

## Architecture

```text
Vendor Edition
  │ license / entitlement / package
  ▼
Reseller Edition
  │ delegated provisioning / bounded configuration
  ▼
Customer Edition
  │ isolated tenant / customer operations
  ▼
End Customer Environment
```

No downstream edition may gain implicit access to the control plane of the edition above it.

## Backend

FastAPI, PostgreSQL/SQLAlchemy async, Alembic, Redis, Celery/Beat, JWT authentication, multi-tenancy/RBAC, files, employees/runs, AI gateway, memory, RAG/knowledge, workflows, approvals, schedules/events, billing, invoices, orders, sales/deals, feedback, developer/admin operations, metrics and telemetry.

The API is the source of truth for authorization and tenant isolation. The browser must never be trusted to enforce permissions.

## Frontend

Next.js App Router + React + TypeScript with Auth, Customer Dashboard, Employees, Runs, Files, Knowledge, Memory, Chat, Studio, Workflows, Approvals, Orders, Sales, Billing, Developer/Observability, and Admin surfaces.

## Database rule

The authoritative Alembic graph must remain the source of truth. Run:

```powershell
cd backend
alembic upgrade head
alembic current
alembic heads
alembic check
```

Do not use `alembic stamp` to conceal a mismatch.

## Correct implementation order

1. Infrastructure
2. Backend configuration
3. Database migration
4. Backend startup
5. Authentication and tenant isolation
6. Employees
7. Runs + Celery
8. AI Gateway / provider integration
9. Files
10. Knowledge + Memory
11. Workflows + approvals + schedules
12. Business modules
13. Developer/Admin/Observability
14. Frontend contract tests
15. Frontend live smoke
16. Full E2E
17. Production hardening
18. Release integrity
19. Vendor/Reseller/Customer productization
20. Repeatable delivery package

## Release gates

Package and publish only from an immutable revision whose required evidence is recorded. Re-run only gates affected by later code/configuration changes; do not restart unrelated historical certification work.

## Commercial delivery definition

A delivery is complete only when its exact commit/tag, manifest, evidence, edition boundary, configuration/secrets model, installation, migration, backup/restore, rollback, acceptance criteria, upgrade path, and vendor/reseller/customer responsibilities are documented and reproducible.
