# AI Employee Platform — Productization & Delivery Roadmap

## Purpose

This is the **current authoritative productization roadmap**. It reconciles the implementation, merged PR history, CI evidence and the 2026-08-22 test/documentation work.

The platform is no longer treated as a project whose main remaining work is core-feature construction. The certified software core and most runtime productization foundations are implemented. The current frontier is **operationalization, repeatable delivery and commercial readiness**.

The commercial topology remains:

1. **Vendor Edition** — owned and operated by the primary seller.
2. **Reseller Edition** — operated by an authorized secondary seller.
3. **Customer Edition** — the isolated instance/configuration delivered to an end customer.

Historical RC8/RC9 certification evidence remains valid unless a later change affects the certified behavior. Post-release productization work does not retroactively rewrite the published release.

## Current project position — 2026-08-22

**Overall position: CORE PLATFORM COMPLETE → PRODUCTIZATION FOUNDATION COMPLETE → OPERATIONALIZATION / DELIVERY PACKAGE IN PROGRESS.**

The repository history shows that a substantial amount of work previously represented as pending in older documentation has already been implemented and tested. The current documentation must therefore distinguish:

- implemented runtime behavior;
- tested/CI-certified behavior;
- local production-like evidence;
- deployment-specific production evidence;
- genuinely remaining commercial/operational work.

Do **not** reopen completed phases merely because an older RC/Phase document lists their historical gaps.

## Baseline

- Published release baseline: **v1.0.1** at `2d23a01098f432145ecaea14b2500fe520ad0bf7`.
- `main` contains the post-release productization/release-topology line and is not itself the published release.
- Productization changes must not rewrite `v1.0.1`; the next vendor product release must have a new immutable release identity.
- Reseller/customer changes are delivery revisions referencing an immutable vendor release.
- Dated post-release evidence: `docs/current/08_POST_RELEASE_PRODUCTIZATION_TEST_EVIDENCE_2026-08-22.md`.
- Documentation reconciliation: `docs/current/09_DOCUMENTATION_RECONCILIATION_2026-08-22.md`.

## Evidence classification

Use these states consistently:

- **DONE / IMPLEMENTED** — implementation is present in the current lineage.
- **DONE / TESTED** — implementation has explicit automated or documented verification evidence.
- **DONE / LOCAL** — behavior is observed in a production-like local environment but is not external-production certified.
- **PENDING** — implementation/evidence is genuinely missing.
- **ENVIRONMENT-SPECIFIC** — repository implementation exists, but the real deployment target still requires verification.

A historical failed/cancelled GitHub Actions run is not a current blocker when a later synchronized commit has replaced/fixed the failing state and the current evidence is green.

---

## Phase 0 — Release Integrity

**Status: 🟢 BASELINE COMPLETE; immutable release-publication automation remains.**

- [x] Synchronize README/current documentation with the published release.
- [x] Record the exact `v1.0.1` commit and distinguish it from post-release `main` work.
- [x] Define immutable vendor/release identity as the root of downstream delivery manifests.
- [x] Establish release/certification boundary so productization does not silently reopen RC8/RC9 certification.
- [x] Reconcile current documentation against implementation and recent PR/test evidence.
- [ ] Maintain an immutable release manifest containing version, commit SHA, migration head, artifacts and certification evidence as a release artifact.
- [ ] Keep release notes/changelog generation tied to the exact release tag.

**Exit:** source state, published release identity and current documentation no longer contradict each other.

---

## Phase 1 — Vendor Edition

**Status: 🟢 RUNTIME FOUNDATION IMPLEMENTED; commercial authority/operations remain.**

### Implemented / tested

- [x] Vendor release is the immutable source of truth.
- [x] Vendor delivery manifest references exact release identity.
- [x] Vendor/reseller/customer identities are modeled as delivery identities rather than source forks.
- [x] Vendor control-plane endpoints are restricted to vendor platform administrators.
- [x] Vendor can provision direct reseller tenants.
- [x] Vendor-only provider/global administration boundary is enforced by the application.
- [x] Runtime parent/child and edition-kind constraints are enforced.
- [x] Privileged provisioning/delegation actions use the existing audit path.

### Remaining

- [ ] Product/package and feature-entitlement authority.
- [ ] License issuance/revocation model.
- [ ] Vendor-only operational data/audit expansion where required for commercial operations.
- [ ] Release/version management UI/API.
- [ ] Full provider/global configuration management beyond the current status surface.
- [ ] Vendor observability/support tooling.
- [ ] Signed/immutable delivery-manifest generation.

**Exit:** vendor can commercially manage downstream environments without exposing vendor control-plane capabilities.

---

## Phase 2 — Reseller Edition

**Status: 🟢 RUNTIME CONTROL-PLANE + TENANT LIFECYCLE FOUNDATION COMPLETE; commercial entitlement lifecycle remains.**

### Implemented / tested

- [x] Reseller delivery identity and revision format.
- [x] Reseller manifest referencing immutable vendor release.
- [x] Reseller configuration/branding placeholders.
- [x] Secret and tenant-boundary rules.
- [x] Reseller tenant boundary enforced at runtime.
- [x] Reseller admin role boundary enforced at runtime.
- [x] Customer provisioning/deprovisioning foundation.
- [x] Entitlement/quota delegation from direct parent to direct child.
- [x] Reseller audit trail for provisioning/delegation.
- [x] Support escalation from reseller to vendor.
- [x] Vendor-only operations prohibited at application boundary.
- [x] Customer lifecycle controls: suspend, resume and non-destructive deprovision.
- [x] Deprovisioning blocked while active child tenants remain.
- [x] Deprovisioning disables tenant users while retaining tenant data.

### Remaining

- [ ] Commercial entitlement/license reconciliation.
- [ ] Commercial subscription/plan lifecycle where required.

**Exit:** reseller can independently manage customers while remaining isolated from vendor data and controls.

---

## Phase 3 — Customer Edition

**Status: 🟢 RUNTIME TENANT/RBAC + LIFECYCLE FOUNDATION COMPLETE; operational recovery and supportability remain.**

### Implemented / tested

- [x] Customer delivery identity and revision format.
- [x] Customer manifest referencing vendor release and reseller delivery.
- [x] Customer configuration/branding placeholders.
- [x] Customer secret and tenant-boundary rules.
- [x] Customer hierarchy and direct-parent model.
- [x] Customer admin/user lifecycle foundation through tenant RBAC.
- [x] Data/configuration access remains tenant-scoped.
- [x] No access to reseller/vendor control planes.
- [x] Customer support escalation is upward-only to the direct reseller.
- [x] Suspend/resume/deprovision runtime controls.
- [x] Invalid lifecycle transitions are rejected.
- [x] Deprovisioning is dependency-guarded and non-destructive.
- [x] Lifecycle actions remain auditable.

### Remaining

- [ ] Customer backup/restore procedure and rehearsal.
- [ ] Upgrade and rollback procedure.
- [ ] Customer health/readiness diagnostics.
- [ ] Customer audit/export capabilities.
- [ ] Data-retention and restore workflow following deprovisioning.

**Exit:** customer receives a self-contained, supportable product surface with documented recovery procedures.

---

## Phase 4 — Delivery Package

**Status: 🟡 CURRENT IMPLEMENTATION FRONTIER — FOUNDATION COMPLETE; repeatable handoff package remains.**

### Implemented / tested

- [x] Versioned vendor/reseller/customer manifest examples.
- [x] Delivery package directory structure.
- [x] Manifest validation.
- [x] Checksum-protected packaging workflow.
- [x] Delivery package specification and verification rules.
- [x] Delivery topology documentation.
- [x] Current handoff/test evidence is documented separately.

### Next implementation slice

- [ ] Versioned distributable artifact/package containing approved runtime artifacts.
- [ ] Release manifest and checksums for the complete package.
- [ ] Environment/configuration template generation from approved inputs.
- [ ] Installation runbook.
- [ ] Migration/upgrade runbook.
- [ ] Backup/restore runbook.
- [ ] Rollback runbook.
- [ ] Customer acceptance checklist.
- [ ] Security/secrets checklist.
- [ ] Compatibility matrix.
- [ ] Vendor → reseller → customer handoff document.

**Exit:** a new customer environment can be delivered from the documented package without repository-specific improvisation.

---

## Phase 5 — Commercial Production

**Status: 🟡 NOT COMPLETE — depends on Phase 3/4 operational evidence and commercial controls.**

- [ ] License/entitlement enforcement at execution boundaries.
- [ ] Subscription/plan lifecycle where applicable.
- [ ] Upgrade channel and supported-version policy.
- [ ] Security/update policy.
- [ ] Customer support and escalation model.
- [ ] Release channel policy for vendor/reseller/customer editions.
- [ ] Production deployment evidence per real environment.
- [ ] External monitoring/alerting evidence where an actual production target exists.
- [ ] Production rollback/recovery rehearsal.
- [ ] Final production security certification for the actual deployment target.

**Exit:** the platform can be sold, provisioned, upgraded, supported and recovered as a product.

---

## Current evidence map

| Area | Current truth | Primary evidence |
|---|---|---|
| Core certification baseline | 🟢 Complete | `docs/current/05_CERTIFICATION_PROGRESS.md` |
| A–F test sequence | 🟢 Living/current | `docs/current/06_A_F_TEST_TRACKER.md` |
| Current handoff | 🟢 Updated | `docs/current/07_CLIENT_HANDOFF_AND_TEST_EVIDENCE.md` |
| Post-release security/productization | 🟢 Verified | `docs/current/08_POST_RELEASE_PRODUCTIZATION_TEST_EVIDENCE_2026-08-22.md` |
| Documentation reconciliation | 🟢 Reconciled | `docs/current/09_DOCUMENTATION_RECONCILIATION_2026-08-22.md` |
| Vendor/reseller/customer runtime boundaries | 🟢 Implemented | `docs/current/13_RUNTIME_EDITION_BOUNDARIES.md`, `backend/app/services/edition_service.py` |
| Tenant lifecycle | 🟢 Implemented/tested | `backend/app/services/edition_lifecycle_service.py`, lifecycle tests, PR #31 |
| Account password security | 🟢 Implemented/tested | Settings Security / Password, authenticated password-change API, PR #29/#30 |
| Delivery topology | 🟢 Foundation | delivery manifests/package validation and related productization PRs |
| Backup/restore | 🟡 Pending operational evidence | Phase 3/4 remaining work |
| Commercial license lifecycle | 🟡 Pending | Phase 1/2/5 remaining work |
| External production deployment | 🟡 Environment-specific | current handoff deployment gates |

## CI interpretation rule

The Roadmap records **current state**, not every historical GitHub Actions run.

A red/cancelled historical run is not itself a blocker when:

1. a later commit fixes or replaces the failing behavior;
2. the current synchronized branch has green required gates; and
3. the relevant implementation/test evidence is recorded.

Historical CI failures remain useful for debugging history, but they must not regress the roadmap status.

## Cross-cutting acceptance gates

Every phase must preserve:

- Backend-enforced tenant isolation.
- RBAC authorization at API/service boundaries.
- Auditability of privileged actions.
- Secrets excluded from source and distributable artifacts.
- Migration compatibility and a single authoritative Alembic graph.
- Automated CI for ordinary changes.
- Separate production certification/release gates for release candidates.
- Reproducible artifacts from immutable commits.
- Explicit distinction between local production-like evidence and external production evidence.

## Runtime hierarchy

```text
Vendor
  └── Reseller
        └── Customer
```

No downstream edition may gain implicit access to the control plane of the edition above it. Provisioning, entitlement delegation and lifecycle operations require the direct parent/child relationship and expected edition type.

## Release topology

```text
Vendor Edition
    │  license / entitlement / package
    ▼
Reseller Edition
    │  delegated provisioning / bounded configuration
    ▼
Customer Edition
    │  isolated tenant / customer operations
    ▼
End Customer Environment
```

## Definition of Commercially Deliverable

A release is commercially deliverable only when:

- the exact commit/tag is immutable;
- release documentation matches the tag;
- required certification evidence is attached;
- edition boundaries are explicit and enforced;
- installation, migration, backup, restore and rollback are documented;
- secrets/configuration are externalized;
- customer acceptance criteria are executable;
- supported upgrade paths are defined;
- vendor/reseller/customer responsibilities are documented;
- required production-target evidence exists.

## Immediate next phase

**Start with Phase 4 — Delivery Package.**

Phase 2/3 remaining operational items (commercial entitlement, backup/restore, upgrade/rollback, diagnostics, audit/export and retention/restore) should be scheduled as explicit dependencies rather than treated as missing core-platform features.
