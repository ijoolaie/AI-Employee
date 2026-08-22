# Post-Release Productization Test Evidence — 2026-08-22

**Repository:** `ijoolaie/AI-Employee`
**Current main:** `b190e872822c66d0196c71ccde51a6397799f5dc`
**Published release baseline:** `v1.0.1` at `2d23a01098f432145ecaea14b2500fe520ad0bf7`

## Purpose

This document records the productization and account-security work verified after the repository-level RC8/RC9 certification baseline. These changes are post-release work on `main`; they do not retroactively rewrite the published `v1.0.1` release.

## 1. Account security / password change

The authenticated password-change capability was completed and exposed through the customer Settings surface.

### Implemented

- Authenticated password-change service and API endpoint.
- Password-change request/response schemas.
- Dedicated frontend password-change API helper.
- Settings navigation with a **Security / Password** entry.
- `/settings/security` page.
- Password length validation: 8–128 characters.
- New-password confirmation validation.
- Explicit successful-change state and **Sign in again** action.
- Session invalidation/re-authentication flow after a successful password change.

### Verification

- Password reset flow was manually verified successfully by the project owner.
- PR #29 fixed the unrelated guardrail-test fixture regression while exposing the Security / Password entry.
- PR #30 polished the Security / Password UX without changing the authenticated backend contract.
- The final password-security implementation is present on `main` at commit `551abf9238bb64d590310dca0e4c62c0078906d3` and is included in the current main lineage.

**Certification classification:** product/security functionality verified; this is not a new production-security certification claim.

## 2. Tenant lifecycle / productization

PR #31 added the next runtime productization slice for the Vendor → Reseller → Customer hierarchy.

### Implemented

- Active → Suspended transition.
- Active → Deprovisioned transition.
- Suspended → Active transition.
- Suspended → Deprovisioned transition.
- Deprovisioned tenants cannot be reactivated.
- Deprovisioning is blocked while child tenants remain active.
- Deprovisioning disables tenant users while retaining tenant data.
- Direct-parent and edition-kind boundaries remain enforced.
- Lifecycle status is exposed in tenant summaries.
- Privileged lifecycle actions are recorded in the existing audit path.

### Automated evidence

The lifecycle transition and child-dependency guard tests were added to `backend/tests/test_edition_boundaries.py` and the lifecycle implementation is in `backend/app/services/edition_lifecycle_service.py`.

## 3. Backend and runtime test evidence

Current test-session evidence recorded in the A–F tracker:

- `pytest -q /app/tests` → **194 passed, 1 warning**.
- Workflow foundation/approval/trigger subset → **7 passed, 1 warning**.
- Execution hardening/workflow-versioning subset → **8 passed**.
- The only full-suite warning is the Python `crypt` deprecation emitted through Passlib; it is not a test failure.

Local Docker runtime was observed healthy:

- API — healthy
- Frontend — healthy
- PostgreSQL — healthy
- Redis — healthy
- Worker — running
- Beat — running

Recurring worker tasks observed successfully include `outbox.dispatch`, `workflow.schedule_tick`, `workflow.timeout_sweep`, and `workflow.approval_expiry`.

## 4. Migration / certification workflow correction

The Production Certification workflow was corrected so the single-Alembic-head assertion is dynamic rather than tied to the historical `v111releaseidentity` revision.

Current assertion:

`alembic heads | grep -c '(head)'`

The same dynamic single-head assertion is used for the production-like Docker API container.

The current migration graph is expected to resolve to one authoritative head.

## 5. CI / PR evidence

Relevant post-release PR sequence:

- **PR #29** — expose Security / Password in Settings and correct the guardrail-test fixture regression.
- **PR #30** — polish the Security / Password UX and keep the existing authenticated API contract.
- **PR #31** — add Vendor → Reseller → Customer tenant lifecycle controls and transition/child-dependency tests.

The latest `main` commit is PR #31's merge commit, so these changes are now part of the current productization baseline.

## 6. What this evidence does NOT claim

This document does not mark repository-level production certification as newly completed. The existing RC8/RC9 certification evidence remains the certification baseline, and deployment-specific production gates remain separate.

Still-open production-specific areas include real production deployment, real production secrets, external monitoring/alerting, backup/restore rehearsal in the target environment, live payment/webhook verification, and production security certification.

## 7. Next documentation-controlled step

The next authoritative roadmap update must treat the tenant lifecycle implementation as completed runtime foundation work and then reconcile the remaining Reseller/Customer/Delivery Package gaps against the latest project documentation before selecting the next implementation slice.
