# Documentation Reconciliation — 2026-08-22

## Purpose

This document reconciles the current documentation set after the 2026-08-22 test/productization work. It separates historical certification documents from the current post-release productization truth.

## Authoritative document order

1. `docs/current/05_CERTIFICATION_PROGRESS.md` — certification baseline and production-certification boundary.
2. `docs/current/06_A_F_TEST_TRACKER.md` — living A–F test sequence and current test evidence.
3. `docs/current/07_CLIENT_HANDOFF_AND_TEST_EVIDENCE.md` — current handoff/deployment boundary.
4. `docs/current/08_POST_RELEASE_PRODUCTIZATION_TEST_EVIDENCE_2026-08-22.md` — dated evidence for today's post-release changes.
5. `docs/current/PRODUCTIZATION_ROADMAP.md` — current Vendor → Reseller → Customer productization roadmap.
6. `documents/23_AS_BUILT_CURRENT_STATE_v0.6.1.md` and older RC/Phase documents — historical release/as-built evidence; they must not be interpreted as the current productization state when they conflict with the documents above.
7. `docs/production/RC8_IMPLEMENTATION_MATRIX.md` — historical RC8 scope/gap analysis. It remains useful as audit history but is not the current productization roadmap.

## Reconciled facts

### Certification

The RC8/RC9 repository-level certification baseline remains valid. The 2026-08-22 work is post-release productization/security work and is deliberately not represented as a new production-certification pass.

### Current automated evidence

- Backend full suite: **194 passed, 1 warning**.
- Workflow foundation/approval/trigger subset: **7 passed, 1 warning**.
- Execution hardening/workflow-versioning subset: **8 passed**.
- Docker API/frontend/PostgreSQL/Redis/Worker/Beat local runtime observed healthy.
- The only full-suite warning is Passlib's Python `crypt` deprecation.

### Account security

The customer Settings surface now exposes **Security / Password**, backed by the authenticated password-change API. The password-change UX validates the 8–128 character range, confirmation matching and successful re-authentication flow. Password reset was also manually verified successfully by the project owner.

### Productization lifecycle

The Vendor → Reseller → Customer runtime hierarchy now includes bounded lifecycle operations:

- active → suspended;
- active → deprovisioned;
- suspended → active;
- suspended → deprovisioned;
- deprovisioned cannot be reactivated;
- deprovisioning is blocked while child tenants remain active;
- tenant users are disabled on deprovisioning;
- tenant data is retained rather than destructively deleted;
- lifecycle operations remain direct-parent/edition constrained and auditable.

## Documentation conflicts resolved

### Conflict 1 — Phase 2 lifecycle status

The productization roadmap previously marked full customer lifecycle/suspension/deprovisioning as pending. PR #31 implemented the runtime lifecycle controls and transition/child-dependency tests.

**Resolution:** Roadmap now marks the runtime lifecycle controls complete and leaves only commercial entitlement/license reconciliation pending for Phase 2.

### Conflict 2 — Phase 3 deprovisioning status

The roadmap previously marked the whole customer deprovisioning/data-retention item pending. Runtime deprovisioning now exists, but backup/restore and retention/restore procedures do not.

**Resolution:** Runtime suspend/resume/deprovision is marked complete; data-retention/restore remains pending as an operational procedure.

### Conflict 3 — Certification versus post-release changes

The certification progress document was based on 2026-08-20 and could be misread as covering later changes.

**Resolution:** It now explicitly states that 2026-08-22 password-security and lifecycle work is post-release verification and does not constitute a new production-certification claim.

### Conflict 4 — Historical as-built documents

`documents/23_AS_BUILT_CURRENT_STATE_v0.6.1.md` describes an older Employee/Stripe/Invoice sequence and predates the current v1.0.1 productization model.

**Resolution:** It remains historical. The current productization truth is controlled by `docs/current/PRODUCTIZATION_ROADMAP.md` and the current evidence documents; the historical document is not rewritten to manufacture a false historical state.

### Conflict 5 — Historical RC8 implementation matrix

`docs/production/RC8_IMPLEMENTATION_MATRIX.md` contains an older Phase 0–7 gap analysis and explicitly records the state of the project during the RC8 architecture audit.

**Resolution:** It remains an audit/history document. Its old phase numbering and gaps must not override the current productization roadmap.

## Current project position after reconciliation

The project is no longer at the old "RC certification only" position. The published release remains `v1.0.1`, while `main` is the post-release productization line.

The current productization state is:

- **Phase 0:** release-integrity baseline established; final immutable release-manifest/release-publication tasks remain.
- **Phase 1:** Vendor runtime foundation implemented; product/license authority and vendor operations remain.
- **Phase 2:** Reseller runtime foundation and tenant lifecycle controls implemented; commercial entitlement/license reconciliation remains.
- **Phase 3:** Customer tenant/RBAC and lifecycle runtime foundation implemented; backup/restore, upgrade/rollback, diagnostics, audit/export and retention/restore remain.
- **Phase 4:** Delivery-package foundation implemented; repeatable distributable package and operational handoff runbooks remain.
- **Phase 5:** Commercial production is not yet complete.

## Next authoritative planning point

The next implementation decision should be made from the reconciled `PRODUCTIZATION_ROADMAP.md`, not from historical RC8 matrices or old v0.x as-built documents.

The immediate productization frontier is **Phase 4 — Delivery Package**, while the remaining Phase 2/3 operational gaps should be treated as dependencies to schedule explicitly rather than silently assumed complete.
