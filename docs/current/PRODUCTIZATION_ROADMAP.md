# AI Employee Platform — Productization & Delivery Roadmap

## Purpose

This roadmap moves the platform from a certified software release into a repeatable commercial delivery model with three explicitly separated editions:

1. **Vendor Edition** — owned and operated by the primary seller.
2. **Reseller Edition** — operated by an authorized secondary seller.
3. **Customer Edition** — the isolated instance/configuration delivered to an end customer.

Certification evidence is treated as completed unless a later change affects the relevant behavior. This work does not reopen RC8/RC9 certification by default.

## Baseline

- Latest published release: **v1.0.1** at commit `2d23a01098f432145ecaea14b2500fe520ad0bf7`.
- `main` contains post-release productization/release-topology work and is not itself a published release.
- Productization work must never rewrite `v1.0.1`; the next vendor product change requires a new immutable vendor release.
- Reseller/customer changes are delivery revisions referencing an immutable vendor release.

## Phase 0 — Release Integrity

**Status: COMPLETE for the current documentation/release-position work.**

- [x] Synchronize README/current documentation with the published release.
- [x] Record the exact `v1.0.1` commit and the post-release `main` delta.
- [x] Define the next release baseline only after affected CI/release-topology gates are green.
- [x] Define immutable vendor/release identity as the root of downstream delivery manifests.
- [ ] Maintain an immutable release manifest containing version, commit SHA, migration head, artifacts, and certification evidence.
- [ ] Keep release notes and changelog generated from the exact release tag.

**Exit:** published release, source state, and documentation no longer contradict each other for the current handoff.

## Phase 1 — Vendor Edition

**Status: RUNTIME FOUNDATION IMPLEMENTED; global lifecycle/product authority remains pending.**

- [x] Vendor release is the immutable source of truth.
- [x] Vendor delivery manifest references the exact release tag and commit SHA.
- [x] Vendor/reseller/customer identities are explicitly modeled as delivery identities rather than source forks.
- [x] Vendor control-plane endpoints are restricted to vendor platform administrators.
- [x] Vendor can provision direct reseller tenants.
- [x] Vendor-only provider/global administration boundary is enforced by the application.
- [ ] Product/package and feature entitlement authority.
- [ ] License issuance/revocation model.
- [ ] Vendor-only operational data and audit trail expansion.
- [ ] Release/version management UI/API.
- [ ] Global provider/configuration management beyond the read-only status surface.
- [ ] Vendor observability and support tooling.
- [ ] Signed/immutable delivery manifest generation.

**Exit:** vendor can provision and manage downstream environments without exposing vendor control-plane capabilities.

## Phase 2 — Reseller Edition

**Status: RUNTIME CONTROL-PLANE FOUNDATION IMPLEMENTED; commercial lifecycle remains pending.**

- [x] Reseller delivery identity and revision format.
- [x] Reseller manifest referencing immutable vendor release.
- [x] Reseller-specific branding/configuration placeholders.
- [x] Explicit secret and tenant-boundary rules.
- [x] Reseller tenant boundary enforced at runtime.
- [x] Reseller admin role boundary enforced at runtime.
- [x] Customer provisioning/deprovisioning foundation.
- [x] Entitlement/quota delegation from vendor/reseller parent to direct child.
- [x] Reseller audit trail for provisioning and entitlement delegation.
- [x] Support escalation from reseller to vendor.
- [x] Explicit prohibition of vendor-only operations enforced by the application.
- [ ] Full customer lifecycle, suspension and deprovisioning workflow.
- [ ] Commercial entitlement/license reconciliation.

**Exit:** reseller can manage its customers independently while remaining isolated from vendor data and controls.

## Phase 3 — Customer Edition

**Status: RUNTIME TENANT/RBAC FOUNDATION IMPLEMENTED; operational recovery and packaging remain pending.**

- [x] Customer delivery identity and revision format.
- [x] Customer manifest referencing vendor release and reseller delivery.
- [x] Customer-specific configuration/branding placeholders.
- [x] Explicit customer secret and tenant-boundary rules.
- [x] Customer tenant hierarchy and direct-parent model.
- [x] Customer admin/user lifecycle foundation through tenant RBAC.
- [x] Data and configuration access remains tenant-scoped.
- [x] No access to reseller/vendor control planes.
- [x] Customer support escalation is upward-only to the direct reseller.
- [ ] Customer backup/restore procedure.
- [ ] Upgrade and rollback procedure.
- [ ] Customer health/readiness diagnostics.
- [ ] Customer audit/export capabilities.
- [ ] Full customer deprovisioning and data-retention workflow.

**Exit:** customer receives a self-contained, supportable product surface with clear boundaries and recovery procedures.

## Phase 4 — Delivery Package

**Status: FOUNDATION IMPLEMENTED; full repeatable handoff package remains pending.**

- [x] Versioned vendor/reseller/customer manifest examples.
- [x] Delivery package directory structure.
- [x] Manifest validation and checksum-protected packaging workflow.
- [x] Delivery package specification and verification rules.
- [ ] Versioned distributable artifact/package containing approved runtime artifacts.
- [ ] Release manifest and checksums for the complete package.
- [ ] Environment/configuration template generation from approved inputs.
- [ ] Installation runbook.
- [ ] Migration/upgrade runbook.
- [ ] Backup/restore runbook.
- [ ] Rollback runbook.
- [ ] Acceptance checklist.
- [ ] Security/secrets checklist.
- [ ] Compatibility matrix.
- [ ] Handoff document for vendor → reseller → customer.

**Exit:** a new customer environment can be delivered from the documented package without repository-specific improvisation.

## Phase 5 — Commercial Production

**Goal:** operationalize the delivery model.

- [ ] License/entitlement enforcement at execution boundaries.
- [ ] Subscription/plan lifecycle where applicable.
- [ ] Upgrade channel and supported-version policy.
- [ ] Security/update policy.
- [ ] Customer support and escalation model.
- [ ] Release channel policy for vendor/reseller/customer editions.
- [ ] Production deployment evidence per environment.
- [ ] External alerting and rollback evidence where an actual production target exists.

**Exit:** the platform can be sold, provisioned, upgraded, supported, and recovered as a product.

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

## Runtime boundary acceptance

The runtime follow-up is implemented in `docs/current/13_RUNTIME_EDITION_BOUNDARIES.md` and `backend/app/services/edition_service.py`.

The required hierarchy is:

```text
Vendor
  └── Reseller
        └── Customer
```

No downstream edition may gain implicit access to the control plane of the edition above it. Provisioning and entitlement delegation require a direct parent/child relationship and the expected edition type.

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
- the edition boundary is explicit;
- installation, migration, backup, restore, and rollback are documented;
- secrets/configuration are externalized;
- customer acceptance criteria are executable;
- supported upgrade paths are defined;
- vendor/reseller/customer responsibilities are documented.
