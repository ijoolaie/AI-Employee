# Multi-Vendor / RBAC / Portal Source Gap Analysis

**Date:** 2026-11-02  
**Repository source inspected:** `main` at `0c921d85fae806851fad1a58170d37bf8d46114d`  
**Tracking:** [Issue #1350](https://github.com/ijoolaie/AI-Employee/issues/1350)  
**Related engineering evidence:** `docs/current/PHASE_14_RUNTIME_ISOLATION_RBAC_ENGINEERING.md`  
**Status:** Initial source-backed audit; deeper data-surface and migration audit remains open.

## 1. Executive result

The repository already contains a Vendor → Reseller → Customer tenant hierarchy, edition-specific backend guards, child-tenant provisioning, commercial entitlements, separate frontend route groups, and an automated isolation/RBAC test harness. The approved architecture is therefore an extension and correction of existing behavior, not a greenfield replacement.

The current implementation does not yet satisfy the newly approved product rules. The largest confirmed gaps are public signup ownership/lifecycle, default-Vendor resolution, direct Vendor-to-Customer provisioning, per-user permission delegation, cross-portal context authorization, and a complete Vendor portal experience.

No application code, database records, local user accounts or production resources were changed during this audit.

## 2. Source-backed findings

### G1 — Public registration creates a standalone Customer tenant, not a child of the default Vendor

**Evidence:**
- `frontend/app/(auth)/register/page.tsx`: the public form collects organization name, tenant slug, name, email and password. It has no account-type selector or Vendor context.
- `backend/app/schemas/auth.py` (`RegisterRequest`): the request has tenant name/slug and user credentials only; no account type, parent tenant or Vendor selector.
- `backend/app/services/auth_service.py` (`_create_tenant`): creates a Tenant without setting `tenant_kind` or `parent_tenant_id`; the model default is `customer` and the parent is null.
- `backend/app/services/auth_service.py` (`register_tenant_and_user`): creates the first user as active and assigns the tenant Admin role with `DEFAULT_TENANT_ADMIN_PERMISSIONS`.

**Impact:** current public registration cannot distinguish Reseller from Customer and does not attach either to the default Vendor. A newly registered user becomes an administrator of a newly created standalone Customer tenant.

**Required change:** explicit public account type limited to Reseller/Customer, server-side default-Vendor resolution, server-controlled parent ownership, and a pending membership state before activation.

### G2 — Default Vendor selection and authorized Vendor provisioning are not represented in the inspected core model

**Evidence:**
- `backend/app/models/tenant.py`: Tenant has `tenant_kind` and `parent_tenant_id`, but no explicit `is_default` marker or configured default-Vendor reference.
- `backend/app/services/edition_service.py` (`provision_child_tenant`): only accepts Vendor → Reseller and Reseller → Customer provisioning.
- `backend/app/api/v1/edition_control.py`: exposes Vendor → Reseller and Reseller → Customer endpoints; no Vendor-creation/provisioning endpoint is defined in this router.
- Searches of the current source for `default_vendor` and `vendor.create` returned no implementation matches.

**Impact:** multiple root Vendor rows can be represented by the hierarchy, but the authoritative default Vendor selection and safe creation of additional Vendors/initial Vendor Owners are not implemented in the inspected path.

**Required change:** a unique, server-controlled default-Vendor setting/resolver and a separate privileged provisioning workflow for new Vendor tenants and their initial owners. Do not infer default status from the first row or client input.

### G3 — Vendor cannot directly provision a Customer

**Evidence:**
- `backend/app/services/edition_service.py` (`provision_child_tenant`) selects Vendor as the required parent only when `kind == reseller`; all Customer provisioning requires a Reseller parent.
- `backend/app/api/v1/edition_control.py`: exposes `POST /edition/vendor/resellers` and `POST /edition/reseller/customers`; no `POST /edition/vendor/customers` path was found.

**Impact:** the approved direct Vendor → Customer registration/creation path is unavailable.

**Required change:** add a Vendor-authorized direct-Customer creation path while preserving the single-owner invariant and Vendor boundary.

### G4 — Child creation is administrator-role gated, not delegated per user

**Evidence:**
- `backend/app/services/edition_service.py` defines fixed `RESELLER_PERMISSIONS` including `reseller.customer.create`, `reseller.customer.read` and `reseller.customer.manage`.
- `provision_child_tenant` creates a fixed Admin role for the child and attaches the fixed permission set.
- `require_edition` checks the Tenant edition and whether the user is a superuser or has a role named Admin, Owner or tenant_admin. It does not evaluate a per-user grant for the requested child-creation operation.
- `backend/app/core/edition_deps.py` maps API-key scopes for specific control-plane routes, but those API-key scopes do not implement user-specific role delegation for bearer-authenticated users.

**Impact:** the current edition admin gate cannot express the required case where one Reseller user may create Customers and another Reseller user may not. A fixed Admin role is not the requested configurable delegation model.

**Required change:** explicit action permissions and scopes for user/role grants, with a delegation ceiling enforced on both the grant operation and the target operation. Preserve existing role/permission infrastructure where possible.

### G5 — Cross-portal access is explicitly denied today; there is no server-validated portal context

**Evidence:**
- `frontend/lib/portal-access.ts`: `canEnterPortal` returns true only when `accountKind === portal`; it has no grant/permission input.
- `frontend/lib/portal-access.test.ts`: tests assert strict same-kind-only access for Vendor, Reseller and Customer.
- `frontend/app/(vendor)/layout.tsx`, `frontend/app/(reseller)/layout.tsx`, and `frontend/app/(customer)/layout.tsx`: route guards compare the current Tenant kind and redirect mismatched account kinds.
- `backend/app/services/edition_service.py` (`require_edition`) denies requests to any edition other than the authenticated Tenant kind.
- `backend/app/api/v1/auth.py` `/me` returns the authenticated User and Tenant; no portal grants or active portal context are returned.
- `backend/app/services/auth_service.py` issues tokens bound to the user's tenant ID; no separate portal-context claim or context-switch flow is present in the inspected implementation.

**Impact:** Vendor users cannot enter Reseller/Customer portals and Reseller users cannot enter Customer portal, even if the product owner intends to grant that access. Frontend-only changes would not work because backend edition dependencies still reject cross-edition operations.

**Required change:** introduce server-authoritative portal grants and an explicit active Portal Context that never changes primary identity, tenant ownership or the immutable identity ceiling. Add audited context switching and context-aware backend authorization.

### G6 — Vendor portal experience is a placeholder; other portal foundations are more developed

**Evidence:**
- `frontend/app/(vendor)/vendor/dashboard/page.tsx` renders a small Vendor heading and workspace name; it does not provide the approved Vendor management dashboard.
- `frontend/app/(vendor)/layout.tsx` is a minimal shell without the richer Vendor navigation/context controls required by the approved design.
- `frontend/app/(reseller)/reseller/dashboard/page.tsx` contains a separate Reseller dashboard with customer portfolio, service team, AI workforce and support links.
- `frontend/components/layout/reseller-sidebar.tsx` provides a dedicated Reseller navigation and identity area.
- `frontend/app/(customer)/layout.tsx` provides a separate Customer layout and sidebar.

**Impact:** separate route groups exist, but the Vendor portal is not a complete operational workspace. Portal identity indicators exist in parts of the UI but are not yet driven by an authorized multi-portal context.

**Required change:** complete the Vendor dashboard and management navigation; align all three portal shells with server-authorized context and clear account/organization/membership identity.

### G7 — Existing subscription trial is not the approved payment-or-Demo membership gate

**Evidence:**
- `backend/app/services/auth_service.py` immediately creates the User as active and assigns Admin before returning registration tokens.
- `register_tenant_and_user` calls `billing_service.ensure_subscription`.
- `backend/app/services/billing_service.py` (`ensure_subscription`) creates a `trialing` Starter subscription with a 14-day trial when none exists.
- `backend/app/models/tenant.py` has a coarse Tenant status (`active`, `suspended`, `trial`) rather than a complete membership lifecycle.

**Impact:** current registration is immediately usable and starts a generic billing trial; it does not represent the approved pending → verified payment or explicitly granted Demo → active lifecycle. A billing trial must not automatically be treated as a policy-approved Demo entitlement.

**Required change:** define membership/entitlement states and activation rules separately from account creation. Payment activation must be based on verified, idempotent provider evidence; Demo must be explicitly granted, time-bound and feature-limited.

### G8 — Existing isolation evidence is valuable but does not prove the full newly required boundary

**Evidence:**
- `docs/current/PHASE_14_RUNTIME_ISOLATION_RBAC_ENGINEERING.md` documents the `vendor → reseller → customer` hierarchy and CI verification.
- `backend/scripts/e2e_tenant_rbac_verify.py` verifies tenant context, cross-tenant employee read/write rejection, cross-tenant file read/download/delete rejection, same-tenant access, restricted-role enforcement and knowledge-search isolation.
- `backend/app/services/edition_service.py` `assert_direct_child` and `assert_can_access` enforce direct-child relationships for relevant edition operations.
- `backend/app/api/v1/edition_control.py` scopes Vendor reseller listing and Reseller customer listing by direct parent IDs.

**Impact:** there is a real isolation foundation and test harness; however, the reviewed evidence does not by itself establish isolation for every required surface (all search, reports, exports, notifications, caches, background jobs, billing views and all customer-user management), nor does it establish Vendor A/B end-to-end production isolation.

**Required change:** retain the existing Phase 14 harness and extend it with the new actor matrix, portal-context tests and a systematic audit of each data surface. Keep issue #19 open for external-production evidence.

## 3. Confirmed reusable foundations

- Tenant hierarchy: `Tenant.tenant_kind` and `Tenant.parent_tenant_id`.
- User-to-tenant membership: `User.tenant_id` and role relationships.
- Role/permission tables and role-permission/user-role joins.
- Edition-specific backend dependencies and API-key route scopes.
- Direct-child provisioning, lifecycle transitions and entitlement delegation.
- Commercial subscriptions/plans and a provider-neutral billing service.
- Distinct frontend route groups and Reseller/Customer UI components.
- Phase 14 real-stack tenant isolation/RBAC CI verification.

These components should be reused after their gaps are proven; do not introduce parallel Tenant, Role, Permission or Billing systems without a documented reason.

## 4. Initial gap matrix

| Requirement | Source state | Gap / next action |
|---|---|---|
| Multi-Vendor roots | Tenant hierarchy can represent Vendor roots | Add authoritative Vendor provisioning and default-Vendor resolver/uniqueness |
| Public Reseller signup | No account type or parent in RegisterRequest | Add server-owned default Vendor parent assignment |
| Public Customer signup | Creates standalone root Customer | Attach to default Vendor and gate activation |
| Vendor-created Reseller | Existing endpoint | Add per-user delegated permission check |
| Vendor-created direct Customer | No endpoint/path found | Add direct child Customer path |
| Reseller-created Customer | Existing endpoint | Enforce per-user grant and ownership scope |
| No cross-Reseller reads | Direct-parent scoping exists for edition list endpoints | Extend tests/audit to every data surface and indirect inference |
| Vendor/Reseller/Customer portal access | Same-kind-only routing/guards | Add explicit grants and server-validated portal context with immutable ceilings |
| Distinct portal UI | Reseller/Customer foundations; Vendor dashboard placeholder | Complete Vendor UI and align all portals to context |
| Payment or Demo activation | Generic 14-day billing trial | Implement explicit membership and entitlement lifecycle |

## 5. Risks and design decisions to settle during detailed implementation

1. **Default Vendor source of truth:** prefer a unique platform configuration/reference with transactional provisioning; avoid relying on a mutable `is_default` boolean without a uniqueness constraint.
2. **Vendor identity and Platform Admin:** keep Vendor Owner separate from Platform Admin. Vendor Owner has full authority only inside its own Vendor boundary.
3. **Portal context:** lower-portal access must not silently impersonate a child account. Decide whether it is a scoped management view or a separately provisioned customer workspace identity; preserve actor attribution in either case.
4. **Customer ownership:** direct Vendor Customer and Reseller-owned Customer must remain distinguishable, with one active owner path.
5. **Existing registered tenants:** create a reviewed migration/mapping plan. Do not silently re-parent existing tenants or alter the three local test accounts.
6. **Payments:** existing manual/trial billing behavior is not proof of live payment-provider verification. Keep payment activation fail-closed until provider webhook/event handling is validated.

## 6. Recommended implementation order

1. Complete a deeper source audit of registration tests, role/permission management APIs, all edition endpoints, resource queries and background jobs.
2. Write the existing-user and tenant migration plan, including how the current standalone Customer tenants map to the default Vendor.
3. Implement Vendor provisioning/default-Vendor resolution and direct Vendor Customer creation.
4. Implement per-user permission delegation and immutable portal-access ceilings in the backend.
5. Implement public Reseller/Customer registration with pending/payment/Demo membership states.
6. Implement portal context switching and distinct portal UIs.
7. Extend the real-stack acceptance matrix and browser E2E; keep issue #19 as the external production gate.

## 7. Verification limits

This audit is based on source files fetched from the inspected `main` SHA. It is not a live production test, does not inspect production databases, and does not certify every resource query or background job. The local staging runtime and user accounts were not modified. The deeper data-surface audit and local execution of relevant tests remain outstanding.