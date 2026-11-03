# Multi-Vendor delegated authorization implementation contract

**Status:** implementation contract for Issue #1350; not a claim that these controls are already implemented.

## 1. Authorization model

- Tenant hierarchy is authoritative: Vendor owns direct Resellers and direct Customers; Reseller owns only its direct Customers; Customer has no child-tenant authority.
- Every request is authenticated into one tenant context. A client-supplied tenant ID, portal name, URL segment or frontend feature flag never grants access.
- Tenant kind and action permission are separate checks. A user must satisfy both for a control-plane operation.
- Use the existing Role → Permission → User assignment model. A user receives only the union of permissions from roles assigned in their own tenant.
- A permission grant is tenant-local. Global/system roles may be assignable only if their permission set is within the actor's delegation ceiling.
- Keep API-key scopes as an additional restriction; they do not replace bearer-user permissions.

## 2. Required action permissions

| Actor tenant | Action | Permission |
|---|---|---|
| Vendor | Read/manage direct Resellers | `edition.vendor.resellers.read/manage` |
| Vendor | Create direct Reseller | `edition.vendor.resellers.create` |
| Vendor | Read/manage direct Customers | `edition.vendor.customers.read/manage` |
| Vendor | Create direct Customer | `edition.vendor.customers.create` |
| Reseller | Read/manage own direct Customers | `edition.reseller.customers.read/manage` |
| Reseller | Create own direct Customer | `edition.reseller.customers.create` |
| Reseller | Delegate Customer entitlements | `edition.reseller.entitlements.delegate` |
| Customer | Any child-tenant create/manage operation | **Never granted** |

These are action permissions, not role names. An Admin label alone must not bypass a missing action permission on delegated control-plane endpoints. The Vendor's initial system-provisioned owner may receive the full Vendor permission set; subsequent Vendor users are provisioned only by a Vendor actor who has the user-management grant.

## 3. Delegation ceiling

- A tenant administrator may create/update roles and assign roles only within the permissions the actor is explicitly allowed to delegate.
- The permission-set subset check must be applied to role creation, role update, and user-role assignment—not just assignment.
- A Reseller cannot create or delegate Vendor permissions, and cannot grant Customer users permissions outside the Reseller's own allowed Customer permission catalogue.
- A Customer cannot create roles that include edition-control permissions.
- Platform-admin status and superuser status are never selectable in tenant-facing APIs. They require a separate trusted platform provisioning path.
- Revoking a role or permission must take effect on the next request; do not rely on stale JWT permission claims.

## 4. User lifecycle

- Tenant user management is distinct from child-tenant provisioning. A child tenant has its own tenant boundary and initial owner; additional staff accounts belong to that same tenant.
- User create/invite endpoints are scoped to the actor's current tenant and require `tenant.users.create`. Role assignment requires `tenant.users.roles.assign`; activation/deactivation requires `tenant.users.manage`.
- Invitation creates a pending/inactive account with a single-use, expiring, hashed invitation token. Never accept or return a plaintext password for another person's account.
- Email uniqueness is checked within the tenant unless the product deliberately adopts global identity with explicit multi-tenant memberships. Do not silently attach an existing account to another tenant.
- Audit invitation, acceptance, role changes, activation, revocation and failed authorization without recording secrets or invitation tokens.

## 5. Portal access

Portal access is an additional server-validated capability, not a client-side route decision:
- Vendor portal: Vendor tenant + Vendor portal grant.
- Reseller portal: Vendor tenant + explicit reseller-portal grant, or Reseller tenant + Reseller portal grant.
- Customer portal: Vendor/Reseller tenant + explicit customer-portal grant, or Customer tenant + Customer portal grant.
- A Reseller never receives Vendor portal access. A Customer never receives Vendor or Reseller portal access.
- Cross-portal view-as must retain the actor identity and target tenant, verify direct ownership and explicit grant on every request, and produce an audit event. It must not change the user's tenant membership or weaken row-level tenant scoping.
- Default-deny all unrecognized portal contexts and all sibling/descendant tenant IDs outside the explicitly allowed hierarchy.

## 6. Required test matrix

1. Vendor user with `edition.vendor.resellers.create` can create a direct Reseller; Vendor user without it receives 403.
2. Vendor user with `edition.vendor.customers.create` can create a direct Customer; one without it receives 403.
3. Reseller user with `edition.reseller.customers.create` can create only a direct Customer under their own Reseller.
4. Reseller cannot create a Customer under another Reseller, a Reseller under any Vendor, or read another Reseller's Customer.
5. Customer cannot create child tenants or access Vendor/Reseller portal APIs, even if a client tampers with the portal context.
6. A role containing permissions beyond the actor's delegation ceiling cannot be created, edited or assigned.
7. API-key scope and bearer-user permission checks both apply; wildcard or legacy null scopes do not bypass edition route restrictions.
8. Invitation tokens are single-use, expire, are stored hashed, and never grant platform/superuser flags.
9. Revoked role/permission is denied on the very next authenticated request.
10. Tenant isolation tests cover list, get, update, export, search, websocket, background task and object-storage access—not only control-plane endpoints.

## 7. Implementation sequence

1. Add action-permission dependency factories and replace broad Admin/Owner gates on edition mutation/read routes with tenant-kind + action permission checks.
2. Seed the explicit Vendor and Reseller action permission catalogues. Keep initial Vendor owner bootstrap separate from public signup.
3. Add tenant-local role create/update endpoints with the delegation-ceiling check.
4. Add secure user invitation/acceptance and user-management action permissions.
5. Add server-authorized portal context and negative cross-tenant tests.
6. Only then wire registration, billing/demo states and distinct portal UX.

## 8. Rollout and migration

- Preserve existing Vendor/Reseller Admin users by explicitly backfilling the relevant action permissions into their existing Admin roles in a reviewed migration.
- Do not infer that every existing non-Admin user should receive child-management permissions.
- Deploy deny-by-default enforcement with migration and rollback notes; test against a dedicated PostgreSQL database before staging/production.
- No production permission backfill or account changes are authorized by this document.
