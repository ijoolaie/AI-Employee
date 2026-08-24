# AI Employee Platform — Productization & Delivery Roadmap

## Purpose

This is the current authoritative productization roadmap. The platform core is complete; the current frontier is repeatable delivery, operational evidence and commercial readiness.

## Current project position — 2026-08-24

**Overall position: CORE PLATFORM COMPLETE → PRODUCTIZATION FOUNDATION COMPLETE → PHASE 4 DELIVERY PACKAGE IMPLEMENTED / LOCAL VALIDATION COMPLETE → PHASE 5 COMMERCIAL IMPLEMENTATION SUBSTANTIALLY COMPLETE → PHASE 6 EDITION-SEPARATED DELIVERY IMPLEMENTATION IN PROGRESS; EXTERNAL PRODUCTION GATES REMAIN.**

Evidence states remain explicit: implementation is not the same as executed local or external-production evidence.

## Baseline

- Published release baseline: **v1.0.1** at `2d23a01098f432145ecaea14b2500fe520ad0bf7`.
- Productization changes must not rewrite `v1.0.1`; the next vendor release needs a new immutable identity.
- Reseller/customer changes are delivery revisions referencing an immutable vendor release.

## Phase 0 — Release Integrity

**Status: 🟢 BASELINE COMPLETE.**

- [x] Synchronize current documentation with published release.
- [x] Record exact v1.0.1 identity.
- [x] Define immutable vendor/release identity.
- [x] Establish certification/productization boundary.
- [x] Release notes/changelog generation tied to the exact release ref.

Implementation: `scripts/generate_release_notes.py` and `.github/workflows/release-artifact.yml` generate `dist/release/RELEASE_NOTES.md` from the exact checked-out release ref and attach it to the release artifact.

## Phase 1 — Vendor Edition

**Status: 🟢 RUNTIME + COMMERCIAL FOUNDATION IMPLEMENTED; remaining work is operational authority/tooling.**

Implemented vendor runtime boundaries, provisioning, license authority, entitlement authority and audit path. Remaining work includes release-management UI/API, broader provider/global configuration management and vendor support tooling.

## Phase 2 — Reseller Edition

**Status: 🟢 RUNTIME CONTROL-PLANE + TENANT LIFECYCLE + COMMERCIAL ENTITLEMENT FOUNDATION COMPLETE.**

Runtime reseller identity, isolation, provisioning/deprovisioning, quota delegation, license control, audit and support escalation are implemented. Subscription/plan state is enforced through the billing service; commercial operations still require real production evidence.

## Phase 3 — Customer Edition

**Status: 🟢 RUNTIME TENANT/RBAC + LIFECYCLE FOUNDATION COMPLETE; production operational evidence remains.**

Customer isolation, RBAC, lifecycle, auditability and support boundaries are implemented. Backup/restore, upgrade/rollback and recovery behavior now have local exercised evidence; external customer-environment evidence remains separate.

## Phase 4 — Delivery Package

**Status: 🟢 IMPLEMENTED / LOCAL VALIDATION COMPLETE.**

### 4A — Release Artifact

- [x] Versioned distributable runtime package.
- [x] Exact source commit/tag identity.
- [x] Migration head recorded.
- [x] File inventory and secret policy.
- [x] SHA-256 checksum generation.
- [x] Release artifact workflow.
- [x] Release notes/changelog generated from the exact release ref.

Primary implementation: `scripts/build_release_package.py`, `.github/workflows/release-artifact.yml`, `scripts/generate_release_notes.py`, `docs/current/14_RELEASE_ARTIFACT_PACKAGE.md`.

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
- [x] Local PostgreSQL/Redis restore smoke rehearsal executed successfully on 2026-08-23.

Primary document: `docs/current/18_BACKUP_RESTORE_RUNBOOK.md`.

### 4F — Rollback

- [x] Rollback triggers documented.
- [x] Known-good artifact/checksum procedure documented.
- [x] Migration-safe rollback guardrails documented.
- [x] Recovery acceptance criteria documented.
- [x] Local controlled recovery/rollback drill executed successfully on 2026-08-23.

Primary document: `docs/current/19_ROLLBACK_RUNBOOK.md`.

### 4G — Customer Acceptance

- [x] Release identity checklist.
- [x] Infrastructure/application acceptance checks.
- [x] Operations/recovery checks.
- [x] Customer/operator sign-off record structure.

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
- [x] Complete local production-like delivery flow exercised.
- [x] Backup/restore rehearsal executed locally — PostgreSQL/Redis smoke path passed on 2026-08-23.
- [x] Rollback/recovery rehearsal executed locally — controlled recovery drill passed on 2026-08-23.
- [x] Final acceptance checklist documented and evidence boundary recorded.
- [ ] Execute release artifact workflow in GitHub Actions when Actions capacity is available.

Primary gate: `docs/current/24_PHASE4_DELIVERY_ACCEPTANCE.md`.

**Exit:** implementation and local validation are complete; production-target evidence remains environment-specific.

## Phase 5 — Commercial Production

**Status: 🟡 IMPLEMENTATION SUBSTANTIALLY COMPLETE; external production evidence and final commercial handoff remain.**

### Implemented / locally exercised

- [x] Commercial license identity with issuer/tenant/edition binding.
- [x] License issuance/revocation service with audit trail.
- [x] Vendor → reseller and reseller → customer license control APIs.
- [x] Fail-closed license check at the run admission boundary.
- [x] Feature entitlement enforcement at the Tool Registry execution boundary.
- [x] Parent-authorized reseller entitlement delegation and quota ceiling.
- [x] Alembic migration for commercial license authority, including explicit grandfathering of existing tenants.
- [x] Subscription lifecycle semantics for trial expiry, cancellation-at-period-end, canceled state and active period renewal.
- [x] Supported-version/release-channel policy and tenant upgrade admission checks for vendor/reseller/customer channels.
- [x] Local full backend suite: **238 passed** on 2026-08-23.
- [x] Local production-like readiness: API, PostgreSQL, Redis and frontend exercised successfully on conflict-safe Windows validation ports.
- [x] Local backup/restore smoke: PostgreSQL logical restore + Redis AOF restore verified.
- [x] Local recovery drill: failure detection and recovery verified against a known-good revision.
- [x] Production environment preparation contract documented.
- [x] Commercial support/update policy and escalation/change-control contract documented.

### Remaining

- [ ] GitHub Actions validation when Actions capacity is available.
- [ ] Real payment/subscriber/revenue evidence for the commercial exit criterion.
- [ ] External production deployment evidence per real environment.
- [ ] External monitoring/alerting evidence.
- [ ] Production-target rollback/recovery rehearsal.
- [ ] Final production security certification.
- [ ] Real customer support/update-policy contacts and environment-specific handoff evidence.

### Preparation contracts

- `docs/current/28_PRODUCTION_ENVIRONMENT_PREPARATION.md`
- `docs/current/29_COMMERCIAL_SUPPORT_UPDATE_POLICY.md`

These documents prepare the external gate but do not claim that an external production target or real commercial deployment exists.

Primary evidence: `docs/current/27_PHASE5_COMMERCIAL_PRODUCTION_EVIDENCE_2026-08-23.md`.

**Exit:** the platform can be sold, provisioned, upgraded, supported and recovered as a product, with remaining external gates separately evidenced for each real production target.

## Phase 6 — Edition-Separated Delivery

**Status: 🟡 IN PROGRESS — profile contracts complete; packaging and local verification being implemented.**

Phase 6 separates the delivery surface into three independently named artifacts while preserving one authoritative codebase and one immutable Vendor source release. It does not create permanent source forks.

### Phase 6A — Contract and nomenclature

- [x] Vendor, Reseller and Customer profile contracts documented.
- [x] Edition release matrix documented.
- [x] Profile-specific authority and rollback rules documented.
- [x] Machine-readable profile contracts added under `delivery/profiles/`.

### Phase 6B — Profile packaging

- [x] Shared-source three-edition builder added: `scripts/build_edition_packages.py`.
- [x] Vendor, Reseller and Customer artifacts use the same vendor commit SHA.
- [x] Secrets are excluded from generated runtime content.
- [x] Edition-specific profile manifests are embedded in each artifact.

### Phase 6C — Local verification

- [x] Edition profile contract tests added: `backend/tests/test_phase6_edition_profiles.py`.
- [x] Machine-readable profile validator added: `scripts/validate_edition_profiles.py`.
- [ ] Execute the builder and archive a local three-edition verification result.

### Phase 6D — Release-system integration

- [ ] Attach Vendor, Reseller and Customer artifacts to the same immutable vendor release in GitHub Actions.
- [ ] Publish per-edition checksums and combined edition release manifest.
- [ ] Verify artifact generation on the first post-reset Actions run.

### Phase 6E — Production delivery

- [ ] Deliver a real Vendor environment.
- [ ] Deliver a real Reseller environment.
- [ ] Deliver a real Customer environment.
- [ ] Capture environment-specific monitoring, recovery, security and handoff evidence.

Primary documentation:

- `docs/current/30_EDITION_RELEASE_MATRIX.md`
- `docs/current/31_VENDOR_RELEASE_PROFILE.md`
- `docs/current/32_RESELLER_RELEASE_PROFILE.md`
- `docs/current/33_CUSTOMER_RELEASE_PROFILE.md`
- `docs/current/34_EDITION_DELIVERY_IMPLEMENTATION_PLAN.md`

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

**Continue Phase 6 — Edition-Separated Delivery in parallel with the remaining Phase 5 external gates. First complete local three-edition package generation/verification; after Actions capacity resets, integrate the three artifacts into the release workflow. Real production deployment, revenue proof, external monitoring/recovery and final security certification remain environment-specific gates.**
