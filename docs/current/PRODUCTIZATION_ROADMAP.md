# AI Employee Platform — Productization & Delivery Roadmap

## Purpose

This is the authoritative productization and delivery roadmap. It distinguishes implementation, CI/release verification, and external-production evidence. The repository has progressed beyond the original 2026-08-24 roadmap snapshot through the V1.4 gap-closure sequence merged after the V1.4 blueprint freeze.

## Current project position — 2026-08-26

**Overall position: CORE PLATFORM COMPLETE → PRODUCTIZATION FOUNDATION COMPLETE → PHASE 4 DELIVERY PACKAGE IMPLEMENTED / LOCAL VALIDATION COMPLETE → PHASE 5 COMMERCIAL IMPLEMENTATION SUBSTANTIALLY COMPLETE → PHASE 6A–6D VERIFIED → PHASE 6E READY FOR EXTERNAL PRODUCTION EXECUTION → V1.4 GAP-CLOSURE IMPLEMENTATION IN PROGRESS.**

The V1.4 blueprint is frozen. Implementation is no longer only planned: the dependency-ordered gap-closure sequence has begun and PRs #69–#73 have been completed, with #73 merged after its CI/test correction. This does **not** change the separate production-evidence boundary: no external production claim is made without target-specific evidence.

## Baseline

- Published productization baseline: **v1.0.1** at `2d23a01098f432145ecaea14b2500fe520ad0bf7`.
- Certified controlled-deployment release: **v1.2.0**; release artifact evidence is recorded in the release certification documents.
- Productization changes do not rewrite immutable vendor releases.
- Reseller/customer changes remain delivery revisions referencing an immutable vendor release.

## Phase 0 — Release Integrity

**Status: 🟢 BASELINE COMPLETE.**

Release identity, certification boundary, immutable vendor identity and release-linked documentation are established.

## Phase 1 — Vendor Edition

**Status: 🟢 RUNTIME + COMMERCIAL FOUNDATION IMPLEMENTED; remaining work is operational authority/tooling.**

Vendor runtime boundaries, provisioning, license authority, entitlement authority and audit path are implemented. Remaining work includes release-management UI/API, broader provider/global configuration management and vendor support tooling.

## Phase 2 — Reseller Edition

**Status: 🟢 RUNTIME CONTROL-PLANE + TENANT LIFECYCLE + COMMERCIAL ENTITLEMENT FOUNDATION COMPLETE.**

Runtime reseller identity, isolation, provisioning/deprovisioning, quota delegation, license control, audit and support escalation are implemented. Commercial operations still require real production evidence.

## Phase 3 — Customer Edition

**Status: 🟢 RUNTIME TENANT/RBAC + LIFECYCLE FOUNDATION COMPLETE; external production evidence remains.**

Customer isolation, RBAC, lifecycle, auditability and support boundaries are implemented. Local backup/restore, upgrade/rollback and recovery evidence exists; external customer-environment evidence remains separate.

## Phase 4 — Delivery Package

**Status: 🟢 IMPLEMENTED / LOCAL VALIDATION COMPLETE.**

The delivery package covers release artifacts, configuration, installation, migration/upgrade, backup/restore, rollback, acceptance, security/secrets, compatibility and Vendor → Reseller → Customer handoff.

## Phase 5 — Commercial Production

**Status: 🟡 IMPLEMENTATION SUBSTANTIALLY COMPLETE; external production evidence and final commercial handoff remain.**

Remaining gates are real payment/subscriber/revenue evidence, external deployment, monitoring/alerting, production rollback/recovery, final security certification and environment-specific support/handoff evidence.

## Phase 6 — Edition-Separated Delivery

**Status: 🟢 6A–6D COMPLETE; 6E READY FOR EXTERNAL EXECUTION.**

Phase 6 provides three independently named delivery artifacts while preserving one authoritative codebase and one immutable Vendor source release. It does not create permanent source forks.

### Phase 6A — Contract and nomenclature

**Status: 🟢 COMPLETE.**

Vendor, Reseller and Customer profile contracts, release matrix, authority/rollback rules and machine-readable profile contracts are documented.

### Phase 6B — Profile packaging

**Status: 🟢 COMPLETE — LOCAL VERIFIED.**

Shared-source three-edition builder, common Vendor source SHA, secret exclusion, profile manifests and local package generation are complete.

### Phase 6C — Local verification

**Status: 🟢 COMPLETE — LOCAL VERIFIED 2026-08-24.**

Profile contract tests, machine-readable validation, three-artifact generation, package validation and SHA-256 evidence are complete.

### Phase 6D — Release-system integration

**Status: 🟢 COMPLETE — GITHUB ACTIONS VERIFIED 2026-08-24.**

Verified release artifact run:

```text
run_id       = 32738347495
job_id       = 97466534302
release      = v1.2.0
source_sha   = c329929f1c7e972f626b7ee749c8a2f05a85eace
migration_head = p5license02
```

Verified artifacts and edition checksums remain recorded in the release certification evidence.

### Phase 6E — Production delivery

**Status: 🟡 READY FOR EXTERNAL EXECUTION — NO PRODUCTION CLAIM YET.**

The execution contract is documented in `docs/current/36_PHASE6E_PRODUCTION_DELIVERY_RUNBOOK.md`.

Mandatory delivery order:

1. Vendor environment.
2. Reseller environment.
3. Customer environment.

For each real environment, evidence must cover installation/health, migration state, security posture, monitoring/alerting, backup/recovery, edition-specific authority boundaries, and operator handoff/acceptance.

Open Phase 6E gates:

- [ ] Deliver a real Vendor environment.
- [ ] Capture Vendor production evidence.
- [ ] Deliver a real Reseller environment through the authorized Vendor path.
- [ ] Capture Reseller production evidence.
- [ ] Deliver a real Customer environment through the authorized upstream path.
- [ ] Capture Customer production evidence.
- [ ] Complete production-target recovery/rollback rehearsal.
- [ ] Complete environment-specific security certification.

**Evidence boundary:** GitHub Actions proves reproducible release packaging and verification; it does not prove deployment to a real production target.

## V1.4 — Architecture and Gap Closure

**Status: 🟡 BLUEPRINT FROZEN; DEPENDENCY-ORDERED IMPLEMENTATION IN PROGRESS.**

The V1.4 Master Blueprint and Freeze Record define the architectural baseline. The first implementation wave has been executed as a dependency-ordered PR chain:

```text
#69  Tenant / Worker Context              ✅ complete
#70  Knowledge Tenant Isolation           ✅ complete
#71  Conversation Tenant Isolation        ✅ complete
#72  Scoped API Keys                      ✅ complete
#73  Idempotent Usage Event Ledger        ✅ MERGED
```

These changes establish that V1.4 is an active implementation track, not merely a future plan. Subsequent slices must continue to follow the frozen dependency graph and preserve the distinction between planned, implemented, verified and externally evidenced states.

### V1.4 governance state

- [x] Blueprint frozen.
- [x] Initial dependency-ordered gap closure executed.
- [x] PR #73 merged with verification.
- [ ] Reconcile and determine disposition of older/open planning PRs before treating the GitHub PR queue as the authoritative execution ledger.
- [ ] Continue next dependency-ordered V1.4 slice only after documentation/PR reconciliation checkpoint.

## Cross-cutting acceptance gates

Every phase preserves:

- Backend-enforced tenant isolation.
- RBAC at API/service boundaries.
- Auditability of privileged actions.
- Secrets excluded from source and distributable artifacts.
- One authoritative Alembic graph.
- Fast CI for ordinary changes.
- Separate release certification gates.
- Reproducible artifacts from immutable commits.
- Explicit distinction between local, CI and external-production evidence.

## Runtime hierarchy

```text
Vendor
  └── Reseller
        └── Customer
```

No downstream edition may gain implicit access to the control plane of the edition above it.

## Definition of Commercially Deliverable

A release is commercially deliverable only when the exact release identity is immutable, certification evidence is attached, edition boundaries are enforced, installation/migration/backup/restore/rollback are executable, secrets/configuration are externalized, acceptance criteria are executable, upgrade paths are defined, responsibilities are documented, and required production-target evidence exists.

## Immediate next action

**Documentation/PR reconciliation is the current checkpoint. After that checkpoint, continue V1.4 gap closure in dependency order and execute Phase 6E against real infrastructure in the order Vendor → Reseller → Customer. Do not mark 6E complete or claim commercial go-live until environment-specific production evidence is attached for all required gates.**
