# AI Employee Platform — Productization & Delivery Roadmap

## Purpose

This roadmap moves the platform from a certified software release into a repeatable commercial delivery model with three explicitly separated editions:

1. **Vendor Edition** — owned and operated by the primary seller.
2. **Reseller Edition** — operated by an authorized secondary seller.
3. **Customer Edition** — the isolated instance/configuration delivered to an end customer.

The roadmap treats certification evidence as completed unless a later change affects the relevant behavior. It does not reopen RC8/RC9 certification by default.

## Baseline

- Latest published release: **v1.0.1**.
- `main` contains subsequent release-topology/CI work and must be intentionally versioned before the next customer-delivery release.
- Release documentation must always distinguish **published release**, **current main**, and **certified delivery baseline**.

## Phase 0 — Release Integrity

**Goal:** make the repository internally consistent before productization work.

- [ ] Synchronize README/current documentation with the published release.
- [ ] Record the exact `v1.0.1` commit and the post-release `main` delta.
- [ ] Define the next release baseline only after affected CI/release-topology changes are green.
- [ ] Maintain an immutable release manifest containing version, commit SHA, migration head, artifacts, and certification evidence.
- [ ] Keep release notes and changelog generated from the exact release tag.

**Exit:** published release, source state, and documentation no longer contradict each other.

## Phase 1 — Vendor Edition

**Goal:** establish the primary seller control plane.

- [ ] Vendor identity and global administration.
- [ ] Product/package and feature entitlement authority.
- [ ] License issuance/revocation model.
- [ ] Vendor-only operational data and audit trail.
- [ ] Release/version management.
- [ ] Global provider/configuration management.
- [ ] Vendor observability and support tooling.
- [ ] Signed/immutable delivery manifest generation.

**Exit:** vendor can provision and manage downstream environments without exposing vendor control-plane capabilities.

## Phase 2 — Reseller Edition

**Goal:** allow a secondary seller to operate within a bounded commercial tenant.

- [ ] Reseller tenant boundary.
- [ ] Reseller admin roles and RBAC.
- [ ] Customer provisioning/deprovisioning.
- [ ] Reseller-specific branding/configuration.
- [ ] Entitlement/quota delegation from vendor.
- [ ] Reseller audit trail.
- [ ] Support escalation from reseller to vendor.
- [ ] Explicit prohibition of vendor-only operations.

**Exit:** reseller can manage its customers independently while remaining isolated from vendor data and controls.

## Phase 3 — Customer Edition

**Goal:** provide a clean, isolated, supportable customer deployment.

- [ ] Customer tenant and role model.
- [ ] Customer admin/user lifecycle.
- [ ] Data and configuration isolation.
- [ ] Customer-facing branding/configuration boundaries.
- [ ] Customer backup/restore procedure.
- [ ] Upgrade and rollback procedure.
- [ ] Customer health/readiness diagnostics.
- [ ] Customer audit/export capabilities.
- [ ] No access to reseller/vendor control planes.

**Exit:** customer receives a self-contained, supportable product surface with clear boundaries and recovery procedures.

## Phase 4 — Delivery Package

**Goal:** make delivery repeatable instead of hand-crafted.

- [ ] Versioned distributable artifact/package.
- [ ] Release manifest and checksums.
- [ ] Environment/configuration template.
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

- [ ] License/entitlement enforcement.
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

No downstream edition may gain implicit access to the control plane of the edition above it.

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
