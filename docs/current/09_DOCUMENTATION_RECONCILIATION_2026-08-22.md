# Documentation Reconciliation — 2026-08-22

## Purpose

This document is the reconciliation record for the 2026-08-22 implementation/test review, with a 2026-08-23 evidence addendum. It separates historical certification material from the current productization truth and records what is genuinely complete versus what remains operational/commercial.

## Authoritative document order

1. `docs/current/05_CERTIFICATION_PROGRESS.md` — certification baseline and production-certification boundary.
2. `docs/current/06_A_F_TEST_TRACKER.md` — living A–F test sequence and current test evidence.
3. `docs/current/07_CLIENT_HANDOFF_AND_TEST_EVIDENCE.md` — current handoff/deployment boundary.
4. `docs/current/08_POST_RELEASE_PRODUCTIZATION_TEST_EVIDENCE_2026-08-22.md` — dated evidence for post-release changes.
5. `docs/current/PRODUCTIZATION_ROADMAP.md` — authoritative Vendor → Reseller → Customer productization roadmap.
6. `documents/23_AS_BUILT_CURRENT_STATE_v0.6.1.md` and older RC/Phase documents — historical evidence only.
7. `docs/production/RC8_IMPLEMENTATION_MATRIX.md` — historical RC8 scope/gap analysis only.

## Reconciled facts

### 1. Core platform status

The project has passed the point where the main work is construction of the core SaaS/AI platform. The current repository lineage contains the previously built authentication, tenant/RBAC, employee/run, files/knowledge/memory, commerce and production-like runtime foundations. Older phase documents may therefore show gaps that are historical rather than current.

### 2. Certification status

The RC8/RC9 repository-level certification baseline remains valid. The 2026-08-22 productization/security work and the 2026-08-23 local Employee/EmployeeVersion test work are post-release verification/evidence updates and are not represented as a new production-certification pass.

Published baseline:

`v1.0.1` → `2d23a01098f432145ecaea14b2500fe520ad0bf7`

`main` is the post-release productization line.

### 3. Current automated evidence

Previously documented evidence:

- Backend full suite: **194 passed, 1 warning**.
- Workflow foundation/approval/trigger subset: **7 passed, 1 warning**.
- Execution hardening/workflow-versioning subset: **8 passed**.
- Docker API/frontend/PostgreSQL/Redis/Worker/Beat local runtime observed healthy.
- Recurring Outbox/workflow scheduler/timeout/approval-expiry tasks were observed completing.
- The only full-suite warning is Passlib's Python `crypt` deprecation.

**New 2026-08-23 local evidence:**

- `python -m pytest .\backend\tests\test_employee_api.py -q` → **5 passed**.
- `python -m pytest .\backend\tests -q` → **206 passed** before the final Employee Versioning fixes.
- focused Employee suite (`test_employee_service.py`, `test_employee_versioning.py`, `test_employee_api.py`) → **13 passed in 2.00s** after the fixes.
- full backend suite → **212 passed in 7.89s**.
- `python -m py_compile .\backend\app\services\employee_service.py` → **PASS**.
- `python -m py_compile .\backend\app\api\v1\employees.py` → **PASS**.

The 212-test result is local working-tree evidence from the project owner's 2026-08-23 session. The exact local commit SHA was not captured in the test transcript. It is therefore not a GitHub Actions result and does not create a new repository-level certification checkpoint.

The Employee Versioning work exercised/fixed initial/current version creation, async-compatible mocked `db.add()` handling, sequential publication, current-version switching, and audit resource/metadata expectations. The focused Employee suite and full backend suite are green after those fixes.

A historical red/cancelled CI run is not treated as a current roadmap blocker when a later synchronized change fixes/replaces the behavior and the current evidence is green.

### 4. Account security

The customer Settings surface exposes **Security / Password** backed by the authenticated password-change API.

Verified behavior includes:

- 8–128 character validation;
- confirmation matching;
- successful password-change state;
- sign-in-again/session reauthentication flow;
- password reset manually verified successfully by the project owner.

PR #29 corrected the guardrail-test fixture regression while exposing the Security / Password entry. PR #30 polished the Security / Password UX without changing the authenticated backend contract.

**Current classification: DONE / TESTED.**

### 5. Productization runtime hierarchy

The runtime hierarchy is:

```text
Vendor
  └── Reseller
        └── Customer
```

The application enforces direct parent/child and edition-kind constraints for provisioning, entitlement delegation and lifecycle operations.

### 6. Tenant lifecycle

PR #31 implemented and tested bounded lifecycle operations:

- active → suspended;
- active → deprovisioned;
- suspended → active;
- suspended → deprovisioned;
- deprovisioned cannot be reactivated;
- deprovisioning is blocked while active child tenants remain;
- tenant users are disabled on deprovisioning;
- tenant data is retained rather than destructively deleted;
- lifecycle operations remain direct-parent/edition constrained;
- privileged lifecycle operations use the existing audit path.

**Current classification: DONE / TESTED.**

### 7. Delivery topology

Vendor/reseller/customer delivery identities, manifests, package structure, validation and checksum-protected packaging are implemented as the foundation of the delivery model.

**Current classification: DONE / IMPLEMENTED + TESTED foundation.**

The remaining work is the complete repeatable handoff package, not the basic delivery topology.

## Documentation conflicts resolved

### Conflict 1 — Phase 2 lifecycle status

Older documentation treated customer lifecycle controls as pending.

**Resolution:** runtime suspend/resume/deprovision, dependency guards, user disabling and data retention are complete and tested. Phase 2 now retains only commercial entitlement/license lifecycle work.

### Conflict 2 — Phase 3 deprovisioning status

Older documentation grouped runtime deprovisioning together with operational retention/recovery.

**Resolution:** runtime lifecycle is complete. Backup/restore and retention/restore procedures remain operational gaps.

### Conflict 3 — Security / Password status

The Settings password capability was initially absent from the product surface and was then implemented through PR #29/#30.

**Resolution:** Security / Password is now treated as implemented/tested, not pending.

### Conflict 4 — Historical CI failures

Several historical CI runs were red or cancelled during implementation/debugging.

**Resolution:** roadmap status follows the current synchronized implementation and required green evidence, while historical failures remain useful only as debugging history.

### Conflict 5 — Historical as-built documents

`documents/23_AS_BUILT_CURRENT_STATE_v0.6.1.md` predates the current v1.0.1/post-release productization model.

**Resolution:** it remains historical and is not rewritten to manufacture a new historical state.

### Conflict 6 — Historical RC8 matrix

`docs/production/RC8_IMPLEMENTATION_MATRIX.md` contains an older Phase 0–7 audit model.

**Resolution:** it remains audit/history material and does not override the current productization roadmap.

### Conflict 7 — Backend test-count drift after the 2026-08-23 local session

The prior current evidence recorded **194 passed** for the full backend suite, while the project owner's later local working-tree session reached **212 passed** after Employee Versioning compatibility/audit fixes.

**Resolution:** 212 is recorded as the latest local automated evidence, but it is explicitly classified as local working-tree evidence because no exact local commit SHA or GitHub Actions run was captured. The older 194 result remains historical evidence for the 2026-08-22 session and is not rewritten as though it were the 2026-08-23 result.

## Current project position

The project should now be described as:

> **Certified software core + implemented productization runtime foundation + active operationalization/delivery-package work, with a newer local backend test baseline of 212 passed.**

### Phase status

- **Phase 0:** 🟢 baseline reconciled; immutable release-manifest/release-publication automation remains.
- **Phase 1:** 🟢 vendor runtime foundation implemented; product/license authority and vendor operations remain.
- **Phase 2:** 🟢 reseller runtime foundation and lifecycle controls implemented; commercial entitlement/license lifecycle remains.
- **Phase 3:** 🟢 customer tenant/RBAC/lifecycle runtime foundation implemented; backup/restore, upgrade/rollback, diagnostics, audit/export and retention/restore remain.
- **Phase 4:** 🟡 current implementation frontier; delivery-package foundation exists, repeatable distributable package and runbooks remain.
- **Phase 5:** 🟡 commercial production not complete.

## Remaining work — authoritative list

The following items are the actual remaining productization frontier identified by the reconciliation:

1. Immutable release manifest/release-publication automation.
2. Vendor product/package entitlement authority.
3. License issuance/revocation and commercial entitlement reconciliation.
4. Vendor operational observability/support tooling.
5. Customer backup/restore and recovery rehearsal.
6. Upgrade/rollback procedures and evidence.
7. Customer health/readiness diagnostics.
8. Customer audit/export capability where required.
9. Retention/restore workflow after deprovisioning.
10. Complete versioned distributable delivery package.
11. Complete installation/migration/backup/rollback runbooks.
12. Acceptance/security/secrets/compatibility checklists.
13. Vendor → reseller → customer handoff package.
14. Execution-boundary license/entitlement enforcement.
15. Supported upgrade channel/version policy.
16. Production-target deployment, monitoring, rollback and security evidence.

These are **not** a request to rebuild the core platform.

## Next authoritative planning point

Implementation should proceed from `docs/current/PRODUCTIZATION_ROADMAP.md`.

The immediate implementation frontier is:

**Phase 4 — Delivery Package**

with the Phase 2/3 operational gaps scheduled explicitly as dependencies.
