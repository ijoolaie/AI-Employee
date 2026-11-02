# Multi-Vendor Account, RBAC and Portal Architecture

**Date:** 2026-11-02  
**Status:** Architecture approved; source-backed gap analysis is the next engineering step.  
**Tracking:** [Issue #1350](https://github.com/ijoolaie/AI-Employee/issues/1350)  
**Repository baseline:** `main` at `0c921d85fae806851fad1a58170d37bf8d46114d`

## 1. Approved decisions

- The platform starts with one default Vendor and supports multiple independent Vendors from the beginning.
- Public Reseller and Customer registrations attach to the default Vendor.
- Public Vendor registration is prohibited. Vendor creation and initial Vendor Owner provisioning require an authorized provisioning path.
- Vendor users with explicit permissions may create and manage Resellers and Customers within their Vendor boundary.
- A Reseller with explicit permission may create and manage only its own direct Customers and customer users.
- A Customer may be a direct child of a Vendor or a child of one Reseller. Each Customer has exactly one active owner path.
- Reseller-to-Reseller access is prohibited, including read, enumeration, search, analytics, export, file access and indirect inference.
- Primary identity, permissions and active portal context are separate concepts.
- Vendor users may enter Vendor, Reseller or Customer portals only when the corresponding portal grant exists.
- Reseller users may enter Reseller and Customer portals only when the corresponding portal grant exists; Vendor portal access is categorically prohibited.
- Customer users may enter only the Customer portal, regardless of assigned role or permission.
- Vendor, Reseller and Customer portals require distinct workflows, navigation, dashboards and visual identity.
- Public signup creates a pending membership. Operational activation requires verified payment or an explicitly granted Demo entitlement.

## 2. Logical hierarchy and ownership

```text
Platform provisioning
  ├── Vendor A (default)
  │    ├── Vendor users
  │    ├── Reseller A1
  │    │    └── Customer accounts owned by A1
  │    └── Direct Customer accounts
  └── Vendor B (independent)
       ├── Vendor users
       ├── Reseller B1
       │    └── Customer accounts owned by B1
       └── Direct Customer accounts
```

Every tenant-scoped membership/resource must resolve to exactly one owning Vendor. A Customer may additionally have one direct Reseller parent. Ownership must be represented by stable IDs and database constraints, not inferred from a user-selected role, URL, email domain or frontend state.

Vendor A must not gain visibility into Vendor B merely because both are platform Vendors. Any platform-wide operational access is a separate Platform Admin capability and is not implied by Vendor Owner.

## 3. Identity, membership, role and portal context

Keep these concepts separate:

1. **Primary identity:** immutable account classification (`VENDOR`, `RESELLER`, `CUSTOMER`) and authentication subject.
2. **Tenant membership:** Vendor ownership and optional direct parent relationship.
3. **Role:** named bundle of permissions within a defined tenant scope.
4. **Permission grant:** explicit action authorization, optionally time-bound and delegable.
5. **Portal access grant:** explicit permission to enter a portal; this does not change primary identity.
6. **Active portal context:** the current UI/workspace selected by the user, validated by the server on every request.
7. **Subscription/entitlement:** whether a membership is pending, in Demo, active, expired, suspended or cancelled.

Portal switching must preserve the authenticated identity and ownership boundary. Where a Vendor or Reseller is permitted to view a lower-level portal context, the system must retain the real actor identity and record the context switch and sensitive actions. No silent or unlogged impersonation.

## 4. Permission model

Use the existing authorization engine where it already meets requirements; extend it rather than creating a parallel RBAC system.

Representative permission keys:

- `users.create`, `users.read`, `users.update`, `users.suspend`, `users.assign_permissions`
- `resellers.create`, `resellers.read`, `resellers.update`, `resellers.suspend`
- `customers.create`, `customers.read`, `customers.update`, `customers.suspend`, `customers.transfer`
- `portal.vendor.access`, `portal.reseller.access`, `portal.customer.access`
- `subscriptions.read`, `subscriptions.create`, `subscriptions.update`, `subscriptions.suspend`, `subscriptions.grant_demo`

Scopes must be server-resolved and bounded. Candidate scope vocabulary: `OWN`, `MANAGED`, `TENANT`, and narrowly reserved `GLOBAL`. Do not assume the labels map directly to existing code until the audit is complete.

Delegation invariant: a principal can grant only permissions and scopes that the principal is explicitly authorized to delegate. A child role cannot grant its own parent or platform capabilities. Vendor permissions are always Vendor-scoped; Vendor Owner is not Platform Admin.

## 5. Registration and membership lifecycle

Public signup choices are Reseller or Customer only. Both are attached to the configured default Vendor; public signup must not accept a client-supplied Vendor ID as authoritative.

Suggested lifecycle:

`PENDING` → (`DEMO` or `PAYMENT_PENDING`) → `ACTIVE` → (`EXPIRED` / `SUSPENDED` / `CANCELLED`)

- Demo is granted by an authorized policy or provisioning flow and has explicit duration and feature limits.
- Paid activation requires a verified provider event and an idempotent entitlement update. Do not trust a browser redirect as proof of payment.
- Expired or suspended memberships must be denied protected operations server-side.
- Vendor provisioning is separate from public signup and must atomically establish the Vendor and its initial owner.

## 6. Data isolation and authorization

Authorization must be enforced in the backend and data-access layer, not only in navigation or route guards.

Apply ownership checks to API handlers, ORM queries, search, dashboards, reports, exports, files/downloads, background jobs, notifications, audit views and caches. Use fail-closed behavior when tenant or ownership context is missing or inconsistent.

Security requirements:

- No cross-Reseller read or write access, including ID enumeration and side-channel inference.
- No cross-Vendor access for Vendor users.
- Customer access is limited to its own tenant and explicitly shared resources.
- Child account creation is allowed only when the creator has the corresponding action permission and the requested child scope is within the creator's ownership boundary.
- Permission assignment is constrained by the grantor's delegation ceiling.
- Resource IDs supplied by clients are never sufficient proof of ownership.
- Background jobs must carry an explicit, validated tenant scope.
- Caches and exports must include tenant ownership in their keys and authorization checks.

## 7. Portal UX

### Vendor Portal
- Vendor overview and operational health.
- Reseller lifecycle and direct Customer management.
- Vendor user management, roles and permission delegation.
- Membership, Demo and subscription oversight.
- Vendor-scoped reporting, audit and configuration.

### Reseller Portal
- Reseller profile and performance.
- Own Customer lifecycle and customer-user management.
- Delegated permission management within the Reseller ceiling.
- Own customer subscriptions and reports only.

### Customer Portal
- Customer service/workspace dashboard.
- Customer's own users and account settings.
- Entitlements, subscriptions, invoices and support.

All portals must show a clear account-type marker, organization identity, membership status and current portal context. Navigation and visual design must be purpose-built per portal, not merely the same dashboard with different labels.

## 8. Implementation phases and gates

### Phase 0 — source-backed Gap Analysis (first)
- Inspect tenant models, migrations, ownership constraints and existing tenant hierarchy.
- Inspect user creation, registration, login, token claims and current-user APIs.
- Inspect edition dependencies, RBAC, permission delegation and scope resolution.
- Inspect existing commercial portal/license/entitlement work and all current Vendor/Reseller/Customer UI routes.
- Trace critical API queries for ownership filters, including files, search, reports and background tasks.
- Record code references, tests, gaps, migration risks and reusable components.
- Do not change account records or production data.

**Exit gate:** a file-and-test-referenced gap matrix, with no assumptions based only on docs or UI.

### Phase 1 — data model and provisioning
- Design multi-Vendor-compatible ownership and a unique default-Vendor configuration.
- Define safe initial Vendor Owner provisioning.
- Define membership parent constraints and Customer ownership rules.
- Write a backward-compatible migration and data reconciliation plan.

**Exit gate:** migration review, existing-user mapping plan, and tenant integrity tests.

### Phase 2 — authorization and isolation
- Extend existing RBAC and scope enforcement.
- Add non-escalating permission delegation.
- Add portal access grants and immutable primary-identity ceilings.
- Enforce all backend/data-access boundaries.

**Exit gate:** positive and negative backend tests for Vendor A/B, Reseller A/B and sibling Customers.

### Phase 3 — account management and registration
- Vendor-managed Reseller/Customer creation.
- Reseller-managed direct Customer creation when delegated.
- Public Reseller/Customer signup to the default Vendor.
- Pending, Demo, payment verification and expiration handling.

**Exit gate:** complete signup and admin-provisioning tests without payment-provider assumptions.

### Phase 4 — portal context and distinct UI
- Separate Vendor, Reseller and Customer dashboards and navigation.
- Add server-validated portal switching for explicitly authorized contexts.
- Add clear identity, organization and membership indicators.

**Exit gate:** browser E2E across all allowed and denied portal combinations.

### Phase 5 — security acceptance and rollout
- Test IDOR, tenant enumeration, permission escalation, cross-tenant search/export/file access, cache leakage and background-job scope.
- Run regression and migration tests against isolated staging only.
- Roll out behind controlled feature flags where appropriate.
- Keep external production certification under issue #19 and release promotion under the existing release gates.

**Exit gate:** exact-SHA test evidence, reviewed migration plan, manual portal QA and explicit deployment approval.

## 9. Non-goals and safety boundaries

- This plan does not authorize production deployment, live payment activation, migration of real customer accounts, or modification of the three existing local test users.
- This plan does not replace Platform Admin or issue #19's external production evidence gate.
- CI success is not production certification or customer acceptance.
- Do not duplicate the existing Phase 14 tenant/RBAC implementation without proving a specific gap.
- Do not begin broad UI redesign before backend ownership and authorization contracts are proven.

## 10. Current baseline and next action

- `main`: `0c921d85fae806851fad1a58170d37bf8d46114d`.
- Existing `docs/current/PHASE_14_RUNTIME_ISOLATION_RBAC_ENGINEERING.md` documents a `vendor → reseller → customer` tenant hierarchy, edition dependencies and a real-stack CI verification harness. This is reusable engineering foundation, not proof that all newly approved workflows are complete.
- Existing issue #19 remains an external-production evidence gate.
- New implementation tracker: issue #1350.
- Next action: inspect the actual source code in the isolated Local Staging worktree and publish a source-backed Gap Analysis before application changes.