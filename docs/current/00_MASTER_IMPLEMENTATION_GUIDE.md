# AI Employee Platform — Master Implementation & Delivery Guide
## Published release: 1.0.1

This document is the current implementation guide for the AI Employee Platform. The published `v1.0.1` release is the immutable baseline; `main` may contain subsequent development and must not be treated as part of the release until explicitly tagged.

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
