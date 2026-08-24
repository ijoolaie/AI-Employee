# AI Employee Platform — Productization & Delivery Roadmap

## Purpose

This is the current authoritative productization roadmap. The platform core and release-productization foundation are complete; the current frontier is real production delivery, operational evidence and commercial readiness.

## Current project position — 2026-08-24

**Overall position: CORE PLATFORM COMPLETE → PRODUCTIZATION FOUNDATION COMPLETE → PHASE 4 DELIVERY PACKAGE IMPLEMENTED / LOCAL VALIDATION COMPLETE → PHASE 5 COMMERCIAL IMPLEMENTATION SUBSTANTIALLY COMPLETE → PHASE 6A–6D VERIFIED → PHASE 6E READY FOR EXTERNAL PRODUCTION EXECUTION.**

Evidence states remain explicit: implementation and release validation are not the same as deployment to a real production target.

## Baseline

- Published release baseline: **v1.0.1** at `2d23a01098f432145ecaea14b2500fe520ad0bf7`.
- Productization changes must not rewrite `v1.0.1`; each vendor release has a new immutable identity.
- Reseller/customer changes are delivery revisions referencing an immutable vendor release.

## Phase 0 — Release Integrity

**Status: 🟢 BASELINE COMPLETE.**

- [x] Synchronize current documentation with published release.
- [x] Record exact release identity.
- [x] Define immutable vendor/release identity.
- [x] Establish certification/productization boundary.
- [x] Release notes/changelog generation tied to the exact release ref.

## Phase 1 — Vendor Edition

**Status: 🟢 RUNTIME + COMMERCIAL FOUNDATION IMPLEMENTED; remaining work is operational authority/tooling.**

Implemented vendor runtime boundaries, provisioning, license authority, entitlement authority and audit path. Remaining work includes release-management UI/API, broader provider/global configuration management and vendor support tooling.

## Phase 2 — Reseller Edition

**Status: 🟢 RUNTIME CONTROL-PLANE + TENANT LIFECYCLE + COMMERCIAL ENTITLEMENT FOUNDATION COMPLETE.**

Runtime reseller identity, isolation, provisioning/deprovisioning, quota delegation, license control, audit and support escalation are implemented. Subscription/plan state is enforced through the billing service; commercial operations still require real production evidence.

## Phase 3 — Customer Edition

**Status: 🟢 RUNTIME TENANT/RBAC + LIFECYCLE FOUNDATION COMPLETE; external production evidence remains.**

Customer isolation, RBAC, lifecycle, auditability and support boundaries are implemented. Backup/restore, upgrade/rollback and recovery behavior have local exercised evidence; external customer-environment evidence remains separate.

## Phase 4 — Delivery Package

**Status: 🟢 IMPLEMENTED / LOCAL VALIDATION COMPLETE.**

The delivery package covers release artifact generation, configuration, installation, migration/upgrade, backup/restore, rollback, acceptance, security/secrets, compatibility and Vendor → Reseller → Customer handoff.

## Phase 5 — Commercial Production

**Status: 🟡 IMPLEMENTATION SUBSTANTIALLY COMPLETE; external production evidence and final commercial handoff remain.**

Local implementation, licensing, entitlement enforcement, migration, recovery and production-preparation contracts are complete. Remaining gates are real payment/subscriber/revenue evidence, external deployment, monitoring/alerting, production rollback/recovery, final security certification and environment-specific support/handoff evidence.

## Phase 6 — Edition-Separated Delivery

**Status: 🟢 6A–6D COMPLETE; 6E READY FOR EXTERNAL EXECUTION.**

Phase 6 separates the delivery surface into three independently named artifacts while preserving one authoritative codebase and one immutable Vendor source release. It does not create permanent source forks.

### Phase 6A — Contract and nomenclature

**Status: 🟢 COMPLETE.**

- [x] Vendor, Reseller and Customer profile contracts documented.
- [x] Edition release matrix documented.
- [x] Profile-specific authority and rollback rules documented.
- [x] Machine-readable profile contracts added under `delivery/profiles/`.

### Phase 6B — Profile packaging

**Status: 🟢 COMPLETE — LOCAL VERIFIED.**

- [x] Shared-source three-edition builder added.
- [x] Vendor, Reseller and Customer artifacts use the same vendor commit SHA.
- [x] Secrets are excluded from generated runtime content.
- [x] Edition-specific profile manifests are embedded in each artifact.
- [x] Local three-edition package generation completed on 2026-08-24.

### Phase 6C — Local verification

**Status: 🟢 COMPLETE — LOCAL VERIFIED 2026-08-24.**

- [x] Edition profile contract tests.
- [x] Machine-readable profile validation.
- [x] Three artifacts generated from one source commit.
- [x] Package validation and SHA-256 evidence recorded.

### Phase 6D — Release-system integration

**Status: 🟢 COMPLETE — GITHUB ACTIONS VERIFIED 2026-08-24.**

Verified Release Artifact run:

```text
run_id       = 32738347495
job_id       = 97466534302
release      = v1.2.0
source_sha   = c329929f1c7e972f626b7ee749c8a2f05a85eace
migration_head = p5license02
```

Verified runtime artifact:

```text
name   = ai-employee-v1.2.0-runtime
sha256 = a5e3b43f64f5145c2294b38e650ada0fede664bcbed8c1976dd7a20ffb343d85
```

Verified edition bundle:

```text
name   = ai-employee-v1.2.0-editions
sha256 = bae9941eeb65922d81a6d86141d10dc07cd868c3b924925cbdeeee66721262e0
```

Verified edition checksums:

```text
vendor   = 106e06b8faf430bf96bececdd5c652e81102f349b094628bcfd82c0ae0e55026
reseller = c8140f83d7d6c1c2e9547a9173349036b0c58ec6b229235142bc3a46dabcd484
customer = 12cf516d08997bd6b26d727729fefdce15463daaa933a278a67f37a84a4ff62e
```

Runtime and edition archives were independently inspected for integrity, manifest identity and secret exclusion. All three editions reference the same immutable Vendor source SHA.

### Phase 6E — Production delivery

**Status: 🟡 READY FOR EXTERNAL EXECUTION — NO PRODUCTION CLAIM YET.**

The execution contract is now documented in `docs/current/36_PHASE6E_PRODUCTION_DELIVERY_RUNBOOK.md`.

Delivery order is mandatory:

1. Vendor environment.
2. Reseller environment.
3. Customer environment.

For each real environment, evidence must cover installation/health, migration state, security posture, monitoring/alerting, backup/recovery, edition-specific authority boundaries, and operator handoff/acceptance.

- [ ] Deliver a real Vendor environment.
- [ ] Capture Vendor production evidence.
- [ ] Deliver a real Reseller environment through the authorized Vendor path.
- [ ] Capture Reseller production evidence.
- [ ] Deliver a real Customer environment through the authorized upstream path.
- [ ] Capture Customer production evidence.
- [ ] Complete production-target recovery/rollback rehearsal.
- [ ] Complete environment-specific security certification.

**Important evidence boundary:** GitHub Actions proves reproducible release packaging. It does not prove production deployment.

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

**Execute Phase 6E against real infrastructure in the order Vendor → Reseller → Customer. Do not mark 6E complete until environment-specific evidence is attached for all three delivery paths.**
