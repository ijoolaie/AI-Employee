# Phase 14 — Runtime Isolation & RBAC Engineering Evidence

**Status:** ENGINEERING COMPLETE / EXTERNAL-PENDING  
**Purpose:** make the Vendor → Reseller → Customer runtime-isolation and RBAC boundary continuously verifiable in CI without misrepresenting CI as production certification.

## Implemented boundary

The application models the commercial hierarchy as `vendor → reseller → customer`, with each tenant carrying a `tenant_kind` and optional `parent_tenant_id`. Edition dependencies enforce the expected edition and administrator boundary. Cross-edition access is explicitly restricted to the permitted direct-child relationship.

The existing real-stack certification script `backend/scripts/e2e_tenant_rbac_verify.py` verifies tenant context, cross-tenant employee read/write rejection, cross-tenant file read/download/delete rejection, same-tenant access, restricted-role permission enforcement, and knowledge-search isolation.

## Dedicated CI gate

`.github/workflows/runtime-isolation-rbac-contract.yml` now runs the existing real-stack gate against a fresh Docker Compose PostgreSQL/Redis/API environment on relevant pull requests and manual dispatch. It also verifies the migration graph and asserts that the certification script does not claim production certification.

This is intentionally a **verification harness**, not a second implementation of tenant isolation. The production-certification workflow continues to provide the release-grade, manually/tag-triggered product gate.

## Evidence boundary

A successful CI run proves that the repository's current engineering implementation passes the defined isolation/RBAC scenarios in an ephemeral environment. It does **not** prove:

- Vendor, Reseller, and Customer behavior in an operator-controlled production environment;
- production network/ingress isolation;
- external identity-provider behavior;
- production secret-management controls;
- live paging or operational ownership;
- customer acceptance.

Issue #19 therefore remains **EXTERNAL-PENDING** until the required actor matrix is executed against the accepted immutable release in the real target environment.

## Required external actor matrix

At minimum, external certification must capture positive and negative evidence for:

| Actor | Allowed boundary | Required negative paths |
|---|---|---|
| Vendor administrator | Own vendor control plane; permitted direct reseller administration | Customer access; unrelated reseller access; non-admin vendor access |
| Reseller administrator | Own reseller plus permitted direct customer operations | Vendor control plane; unrelated reseller/customer access |
| Customer administrator/operator | Own customer tenant only | Parent reseller control plane; sibling customer data; unrelated tenant data |

The evidence must bind each result to the exact accepted release SHA/tag and retain request/response status plus tenant/actor identifiers without storing credentials or unnecessary personal data.


## Product Test Scope by Edition

Security isolation and product completeness are separate acceptance dimensions.

The Test Center must verify the following actor boundaries without requiring every actor to exercise every service:

| Actor | Required positive scope | Required negative scope |
|---|---|---|
| Vendor administrator | Own vendor control plane and explicitly authorized direct reseller administration | Customer business workspace by default; unrelated reseller; non-admin vendor |
| Reseller administrator | Own reseller workspace and explicitly authorized direct-child customer operations | Vendor control plane; sibling/unrelated reseller/customer; capabilities not delegated |
| Customer administrator/operator | Own customer workspace and its business capabilities | Parent reseller control plane; sibling customer; unrelated tenant |

Shared tenant isolation/RBAC controls are tested at the authorization boundary. Edition-specific service tests then prove that an authorized actor can perform the capability they own. This avoids duplicating the entire service catalog for Vendor, Reseller and Customer.

Test evidence must identify the edition, tenant, actor, workspace, service group and authorization outcome.
