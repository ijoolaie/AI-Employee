# AI Employee Platform — Productization & Delivery Roadmap

## Purpose

This is the current authoritative productization roadmap. The platform core is complete; the current frontier is repeatable delivery, operational evidence and commercial readiness.

## Current project position — 2026-08-23

**Overall position: CORE PLATFORM COMPLETE → PRODUCTIZATION FOUNDATION COMPLETE → PHASE 4 DELIVERY PACKAGE IMPLEMENTED → LOCAL VALIDATION PENDING.**

Evidence states remain explicit: implementation is not the same as executed local or external-production evidence.

## Baseline

- Published release baseline: **v1.0.1** at `2d23a01098f432145ecaea14b2500fe520ad0bf7`.
- Productization changes must not rewrite `v1.0.1`; the next vendor release needs a new immutable identity.
- Reseller/customer changes are delivery revisions referencing an immutable vendor release.

## Phase 0 — Release Integrity

**Status: 🟢 BASELINE COMPLETE; immutable release-publication automation remains.**

- [x] Synchronize current documentation with published release.
- [x] Record exact v1.0.1 identity.
- [x] Define immutable vendor/release identity.
- [x] Establish certification/productization boundary.
- [ ] Release notes/changelog generation tied to exact release tag.

## Phase 1 — Vendor Edition

**Status: 🟢 RUNTIME FOUNDATION IMPLEMENTED; commercial authority/operations remain.**

Implemented runtime boundaries, vendor provisioning, audit path and provider/global administration boundaries remain complete. Remaining commercial work includes product/feature entitlement authority, license issuance/revocation, release management UI/API, provider/global configuration management and vendor support tooling.

## Phase 2 — Reseller Edition

**Status: 🟢 RUNTIME CONTROL-PLANE + TENANT LIFECYCLE FOUNDATION COMPLETE; commercial entitlement lifecycle remains.**

Runtime reseller identity, isolation, provisioning/deprovisioning, quota delegation, audit and support escalation are implemented. Remaining: commercial entitlement/license reconciliation and subscription/plan lifecycle.

## Phase 3 — Customer Edition

**Status: 🟢 RUNTIME TENANT/RBAC + LIFECYCLE FOUNDATION COMPLETE; operational execution evidence remains.**

Customer isolation, RBAC, lifecycle, auditability and support boundaries are implemented. Operational recovery, diagnostics, audit/export and retention workflows remain execution/evidence dependencies where applicable.

## Phase 4 — Delivery Package

**Status: 🟢 IMPLEMENTED / LOCAL VALIDATION PENDING.**

### 4A — Release Artifact

- [x] Versioned distributable runtime package.
- [x] Exact source commit/tag identity.
- [x] Migration head recorded.
- [x] File inventory and secret policy.
- [x] SHA-256 checksum generation.
- [x] Release artifact workflow.

Primary implementation: `scripts/build_release_package.py`, `.github/workflows/release-artifact.yml`, `docs/current/14_RELEASE_ARTIFACT_PACKAGE.md`.

### 4B — Environment / Configuration

- [x] Approved customer `.env` template.
- [x] Secret-free configuration generator.
- [x] Required vs optional integration rules documented.
- [x] Production Compose configuration contract documented.

Primary implementation: `config/templates/.env.customer.example`, `scripts/generate_customer_config.py`, `docs/current/15_CONFIG_GENERATION.md`.

### 4C — Installation

- [x] Installation prerequisites.
- [x] Release checksum verification.
- [x] Configuration preparation.
- [x] Compose validation.
- [x] Startup and health verification.
- [x] Migration and acceptance handoff.

Primary document: `docs/current/16_INSTALLATION_RUNBOOK.md`.

### 4D — Migration / Upgrade

- [x] Pre-upgrade evidence capture.
- [x] Release and compatibility checks.
- [x] Upgrade procedure.
- [x] Migration-head recording.
- [x] Failure handling and completion record.

Primary document: `docs/current/17_UPGRADE_MIGRATION_RUNBOOK.md`.

### 4E — Backup / Restore

- [x] Backup policy and pre-upgrade backup procedure documented.
- [x] Database and application-storage restore procedure documented.
- [x] Restore acceptance criteria documented.
- [ ] Execute restore rehearsal locally.

Primary document: `docs/current/18_BACKUP_RESTORE_RUNBOOK.md`.

### 4F — Rollback

- [x] Rollback triggers documented.
- [x] Known-good artifact/checksum procedure documented.
- [x] Migration-safe rollback guardrails documented.
- [x] Recovery acceptance criteria documented.
- [ ] Execute rollback rehearsal locally.

Primary document: `docs/current/19_ROLLBACK_RUNBOOK.md`.

### 4G — Customer Acceptance

- [x] Release identity checklist.
- [x] Infrastructure/application acceptance checks.
- [x] Operations/recovery checks.
- [x] Customer/operator sign-off record.

Primary document: `docs/current/20_CUSTOMER_ACCEPTANCE_CHECKLIST.md`.

### 4H — Security / Secrets

- [x] Secret exclusion checks.
- [x] Production secret requirements.
- [x] TLS/CORS/debug checks.
- [x] Integration credential controls.
- [x] Backup/log/access controls.

Primary document: `docs/current/21_SECURITY_SECRETS_CHECKLIST.md`.

### 4I — Compatibility

- [x] Docker/Compose baseline.
- [x] PostgreSQL 16 baseline.
- [x] Redis 7 baseline.
- [x] Python 3.12 and Node 22.x baseline.
- [x] Browser/E2E and external-integration guidance.

Primary document: `docs/current/22_COMPATIBILITY_MATRIX.md`.

### 4J — Vendor → Reseller → Customer Handoff

- [x] Vendor package contents.
- [x] Reseller handoff responsibilities.
- [x] Customer handoff responsibilities.
- [x] Change-control rule for post-handoff modifications.

Primary document: `docs/current/23_HANDOFF_RUNBOOK.md`.

### Phase 4 acceptance gate

- [x] All implementation/documentation slices exist.
- [ ] Execute complete local production-like delivery flow.
- [ ] Execute backup/restore rehearsal.
- [ ] Execute rollback rehearsal.
- [ ] Execute final acceptance checklist.
- [ ] Execute release artifact workflow when Actions quota is available.

Primary gate: `docs/current/24_PHASE4_DELIVERY_ACCEPTANCE.md`.

**Exit:** implementation is complete; local validation is the remaining gate before Phase 5 commercial production work.

## Phase 5 — Commercial Production

**Status: 🟡 NEXT AFTER PHASE 4 LOCAL VALIDATION.**

- [ ] License/entitlement enforcement at execution boundaries.
- [ ] Subscription/plan lifecycle where applicable.
- [ ] Upgrade channel and supported-version policy.
- [ ] Security/update policy.
- [ ] Customer support and escalation model.
- [ ] Release channel policy.
- [ ] Production deployment evidence per real environment.
- [ ] External monitoring/alerting evidence.
- [ ] Production rollback/recovery rehearsal.
- [ ] Final production security certification.

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
- Explicit distinction between local and external-production evidence.

## Runtime hierarchy

```text
Vendor
  └── Reseller
        └── Customer
```

No downstream edition may gain implicit access to the control plane of the edition above it.

## Definition of Commercially Deliverable

A release is commercially deliverable only when the exact release identity is immutable, certification evidence is attached, edition boundaries are enforced, installation/migration/backup/restore/rollback are executable, secrets/configuration are externalized, acceptance criteria are executable, upgrade paths are defined, responsibilities are documented, and required production-target evidence exists.

## Immediate next phase

**Complete the Phase 4 local validation gate, then start Phase 5 — Commercial Production.**
