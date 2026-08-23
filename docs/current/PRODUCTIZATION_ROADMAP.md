# Productization Roadmap

This is the **current authoritative productization roadmap**. It reconciles the implementation, merged PR history, CI evidence and the 2026-08-22/2026-08-23 test/documentation work.

The platform is no longer treated as a project whose main remaining work is core-feature construction. The certified software core and most runtime productization foundations are implemented. The current frontier is **operationalization, repeatable delivery and commercial readiness**.

## Commercial topology

1. **Vendor Edition** — owned and operated by the primary seller.
2. **Reseller Edition** — operated by an authorized secondary seller.
3. **Customer Edition** — the isolated instance/configuration delivered to an end customer.

Historical RC8/RC9 certification evidence remains valid unless a later change affects certified behavior. Post-release productization work does not retroactively rewrite the published release.

## Current local evidence

On 2026-08-23 the project owner recorded **212 passed** for `backend/tests` locally. This is local working-tree evidence, not a GitHub Actions result and not a new production-certification checkpoint.

Phase 4 local validation also passes on the current working tree.

## Phase 0 — Release Integrity

**Status: 🟢 BASELINE COMPLETE; immutable release-publication automation remains.**

- [x] Synchronize README/current documentation with the published release.
- [x] Record the exact `v1.0.1` commit and distinguish it from post-release `main` work.
- [x] Define immutable vendor/release identity as the root of downstream delivery manifests.
- [x] Establish release/certification boundary so productization does not silently reopen RC8/RC9 certification.
- [x] Reconcile current documentation against implementation and recent PR/test evidence.
- [ ] Maintain an immutable release manifest containing version, commit SHA, migration head, artifacts and certification evidence as a release artifact.
- [ ] Keep release notes/changelog generation tied to the exact release tag.

## Phase 1 — Vendor Edition

**Status: 🟢 RUNTIME FOUNDATION IMPLEMENTED; commercial authority/operations remain.**

### Implemented / tested

- [x] Vendor release is the immutable source of truth.
- [x] Vendor delivery manifest references exact release identity.
- [x] Vendor/reseller/customer identities are modeled as delivery identities rather than source forks.
- [x] Vendor control-plane endpoints are restricted to vendor platform administrators.
- [x] Vendor can provision direct reseller tenants.
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

**Status: 🟢 FOUNDATION COMPLETE; repeatable handoff package remains.**

### Implemented / tested

- [x] Versioned vendor/reseller/customer manifest examples.
- [x] Delivery package directory structure.
- [x] Manifest validation.
- [x] Checksum-protected packaging workflow.
- [x] Delivery package specification and verification rules.
- [x] Production compose contract.
- [x] Customer configuration generator smoke test.
- [x] Installation, upgrade/migration, backup/restore and rollback runbooks.
- [x] Security/secrets checklist, compatibility matrix, handoff and acceptance documents.
- [x] Local Phase 4 validation script passes.

**Exit:** delivery artifact can be generated and verified without embedding customer secrets.

---

## Phase 5 — Commercial Production

**Status: 🟡 IMPLEMENTATION IN PROGRESS; production evidence and commercial lifecycle remain.**

### Implemented on the Phase 5 branch; integration validation pending

- [x] Commercial license identity with issuer/tenant/edition binding.
- [x] License issuance and revocation service with audit trail.
- [x] Vendor → reseller and reseller → customer license control APIs.
- [x] Fail-closed license check at the run admission boundary.
- [x] Parent-authorized reseller entitlement delegation and quota ceiling.
- [x] Alembic migration for the commercial license authority, including explicit grandfathering of existing tenants.
- [x] Database-free Phase 5 contract tests.

### Remaining

- [ ] Full integration/runtime test suite after GitHub Actions capacity resets.
- [ ] Entitlement revocation propagation at every feature-specific execution boundary.
- [ ] Complete subscription/plan lifecycle semantics, including unpaid/canceled transitions.
- [ ] Upgrade channel and supported-version policy.
- [ ] Security/update policy.
- [ ] Customer support and escalation operating model.
- [ ] Release channel policy for vendor/reseller/customer editions.
- [ ] Production deployment evidence per real environment.
- [ ] External monitoring/alerting evidence.
- [ ] Production rollback/recovery rehearsal.
- [ ] Final production security certification.

**Exit:** the platform can be sold, provisioned, upgraded, supported and recovered as a product.

## Cross-cutting acceptance gates

Every phase preserves:

- Backend-enforced tenant isolation.
- RBAC at API/service boundaries.
- Auditability of privileged actions.
- Secrets excluded from source and distributable artifacts.
- One authoritative Alembic graph.
- Required production-target evidence exists before commercial completion.

Historical CI failures remain useful for debugging history, but they do not regress roadmap status when later implementation and evidence supersede them.
