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


## Product decision - Vendor parent administration of descendant users (2026-11-20)

**Decision:** The Vendor is the full administrative authority for user lifecycle and access management throughout its own tenant subtree. This resolves the previously open Vendor parent-admin question.

### Scope and non-negotiable boundaries
- A Vendor administrator with the applicable Vendor user-management authority may list, invite, revoke pending invitations, activate/deactivate users, and manage tenant-local role assignments for users in any Reseller or Customer tenant owned directly or indirectly by that Vendor.
- This includes Vendor -> direct Reseller, Vendor -> direct Customer, and Vendor -> Reseller -> Customer paths. Reseller authority remains limited to its own direct Customer children; Vendor authority does not stop at the first child level.
- The target tenant must be resolved from persisted ownership ancestry on every request. Client-supplied tenant IDs, portal context, role names, and UI visibility never establish authority. Sibling Vendors and tenants outside the authenticated Vendor subtree remain inaccessible.
- User records and role assignments remain tenant-local. Parent administration does not move users between tenants or silently attach an existing identity to another tenant.
- Vendor administrators may administer business roles within the target tenant subject to the approved delegation ceiling, but may never grant platform-admin/superuser flags or platform-only permissions. No tenant can grant authority outside its Vendor subtree.
- Invitations remain single-use, expiring, hashed-token flows; no administrator may set or retrieve another user's plaintext password. Last-active-admin safeguards, entitlement checks, API-key scope restrictions, and immediate revocation semantics remain mandatory.
- Every successful lifecycle/role action must be audited with the authenticated Vendor actor, the target tenant, target user/resource, and before/after state as applicable. Existing transaction/privacy policy for failed authorization events remains a separate unresolved decision; do not invent failure-audit semantics.

### Implementation consequence
The existing `reseller_customer_users.py` is only Reseller -> direct Customer and is not sufficient. Implement a shared, hierarchy-aware user-management service and Vendor/Reseller route surfaces rather than copying the narrow router. Extend the acceptance matrix across all three ownership edges and verify same-Vendor descendant access, sibling-Vendor denial, wrong-kind/foreign ancestry denial, role delegation ceilings, last-admin protection, invitation acceptance/revocation, and audit attribution. Do not weaken existing tenant-local identity or platform privilege boundaries.

This is a product-scope decision, not evidence that these routes are already implemented. Issue #1350 remains OPEN until code, tests, exact-head CI and acceptance evidence pass.

## Implementation reconnaissance - hierarchy boundary (2026-11-20)

Source inspection confirms `edition_service.assert_can_access` is intentionally limited to Vendor -> direct Reseller/Customer and Reseller -> direct Customer. `backend/tests/test_edition_boundaries.py::test_vendor_can_access_direct_resellers_and_direct_customers_only` explicitly rejects Vendor -> Reseller -> Customer. Do not broaden this shared cross-edition helper: it is used outside user administration and changing it would expand unrelated API access.

The user-management implementation must therefore use a dedicated, database-backed target resolver that validates the complete persisted ancestry for the user-management routes only. It must support Vendor -> direct Reseller, Vendor -> direct Customer, Vendor -> Reseller -> Customer, and Reseller -> direct Customer; reject sibling Vendor and foreign ancestry; and lock/revalidate the target tenant before writes. The existing `tenant_admin` role loader is also actor-tenant-bound and rejects `vendor.*` permissions, while the Reseller router has a fixed Customer-member role and only list/invite/revoke/status operations. These cannot simply be reused unchanged for Vendor target administration.

No authorization code was changed in this reconnaissance step. The next implementation slice is the dedicated hierarchy resolver plus its unit/PostgreSQL contract tests, followed by target-tenant-aware user lifecycle and role operations with explicit API-key route scopes.
### Vendor delegated user-management resolver — implementation checkpoint (2026-11-20)
- Added `backend/app/services/tenant_user_management_service.py` with a DB-backed resolver that loads actor, target, parent, and (for nested Customer targets) grandparent from persisted `tenants` rows. It rejects inactive tenants, non-root Vendor actors, malformed Reseller ancestry, non-Customer actors, self-targeting, sibling/foreign ancestry, and unsupported hierarchy edges.
- The resolver is intentionally separate from `edition_service.assert_can_access`; no global edition access policy was widened.
- Added `backend/tests/test_tenant_user_management_service.py`; focused pure-policy tests: **8 passed**. `git diff --check` passed.
- Not yet integrated into HTTP routes; no invitation/list/revoke/status/role API behavior changed. No PostgreSQL resolver integration test has run yet.
- An attempted combined run with `test_edition_boundaries.py` had 18 passes and one environment/import failure because the local interpreter is Python 3.10 and an existing module imports `enum.StrEnum` (Python 3.11+); this is not evidence of a product regression. The first attempt also exposed an incorrect test expectation (a Reseller is allowed to manage all its own direct Customers); the test was corrected to use a Customer under a different Reseller.

### Vendor descendant user read APIs — implementation checkpoint (2026-11-20)
- Added `backend/app/api/v1/vendor_tenant_users.py` with target-tenant-scoped GET endpoints for tenant-local users and assignable roles, using the DB-backed ancestry resolver. The route only exposes users whose `User.tenant_id` matches the resolved target; role listing is limited to target-tenant roles and system roles.
- Registered the router and added a dedicated API-key scope `edition.vendor.users.read` with explicit route-template mappings for both GET routes. The API-key scope contract remains fail-closed for unmapped routes.
- Authorization requires the Vendor administrator context plus the target-kind read permission (`vendor.reseller.read` or `vendor.customer.read`). The resolver enforces active target and persisted Vendor subtree ancestry.
- Validation: Python compileall succeeded for changed runtime modules; focused resolver + API-key scope tests: **23 passed**.
- Write operations (invite/revoke/status/role assignment) are not yet exposed for Vendor; no DB-backed live API test has run for these new endpoints. No PostgreSQL or persistent database was touched.

### Validation correction (2026-11-20)
- After adding the new Vendor users read scope to the Vendor API-key allowlist, the final focused run completed with **25 passed** across `test_tenant_user_management_service.py` and `test_edition_api_key_scope_contract.py`; compileall and `git diff --check` also succeeded.

## 2026-11-20 - Write API implementation note
Vendor subtree invitation create/revoke and user activation/deactivation are implemented using persisted ancestry resolution and target-tenant scoping. Mutations use existing invitation security, target tenant/user locks, last-active-admin protection, entitlement-gated reactivation, token-version invalidation, and success audit records in both target and Vendor tenant ledgers. Dedicated API-key scope: `edition.vendor.users.manage`. Role assignment/removal remains gated on a source-backed definition of permitted system roles and permission ceilings; the product prohibition on platform-admin/superuser/platform-only delegation remains absolute.

## 2026-11-20 - Role delegation implementation detail
Vendor role assignment is target-tenant scoped and supports target-local roles plus NULL-tenant system roles only. The complete requested permission set must be a subset of the Vendor actor's explicitly held effective permissions. `vendor.*`, `platform.*`, Platform Admin, and Superuser grants are categorically rejected. Role replacement preserves assignments outside the target tenant and enforces last-active-target-admin protection.

### Vendor user-management authorization revalidation - 2026-11-20
- Source review confirmed that Vendor descendant role replacement already exists in `vendor_tenant_users.py`; it is limited to target-local and NULL-tenant system roles, enforces the existing actor-permission ceiling, blocks `vendor.*`/`platform.*` and named Platform Admin/Superuser grants, preserves non-target assignments, and protects the last active target administrator.
- Found a concurrency gap in write authorization: target tenant was locked, but the Vendor actor's active status and role permissions were not reloaded under lock before mutation. Added `_refresh_vendor_actor` to reload the actor with role permissions and `populate_existing=True` under `FOR UPDATE` after acquiring the target lock; inactive/missing actors now fail closed before the write permission check.
- Validation after the change: `test_tenant_user_management_service.py` + `test_edition_api_key_scope_contract.py`: **34 passed**; `compileall` and `git diff --check` passed. Git emitted existing LF/CRLF warnings only.
- This is focused contract/unit validation, not PostgreSQL/live HTTP acceptance. No database migration, staging/production access, CI, commit, push, or deployment occurred. Existing local worktree changes were preserved.

### Vendor subtree PostgreSQL acceptance attempt and cleanup - 2026-11-20
- Created a dedicated PostgreSQL 16.15 test database on loopback port 15436, with database files on container tmpfs. The complete Alembic migration graph reached head successfully, including `w34_assignment_commands` and `w35_assignment_recovery_claims`.
- Added `backend/tests/test_vendor_tenant_users_live_postgres.py`, a strict disposable-database-only HTTP acceptance covering Vendor reads across direct/nested descendants, foreign-Vendor denial, invitation creation/revocation and hashed token persistence, accepted-invite activation, deactivation, target-local role assignment, last-admin protection, dual-tenant audit attribution, and ledger verification.
- HTTP execution under the default local Python 3.10 stopped at application import because `enum.StrEnum` requires Python 3.11+. Python 3.12 successfully ran the focused DB-free suites: **34 passed**; compileall and `git diff --check` passed. The attempted PostgreSQL HTTP pytest invocation was not completed, so this acceptance remains unverified; do not count it as a pass.
- The disposable PostgreSQL container was stopped and auto-removed; its tmpfs database vanished with it. No persistent Docker volume, staging container, staging/production database, or other container was changed. No generated test database files remain.
- GitHub publication was explicitly requested by the user. Before publishing, preserve branch/PR stacking and inspect the complete dirty worktree; do not merge or deploy. The local worktree contains pre-existing cross-cutting Agent/Outbox/AssignmentCommand changes as well as Vendor user-management work, so publication must not silently omit or discard any of these files.

### GitHub publication checkpoint - 2026-11-20
- Published the Vendor descendant user-management implementation, resolver, API-key route scopes, focused unit/contract tests, disposable-PostgreSQL HTTP acceptance test, and current acceptance/roadmap/handoff documentation in commit `d32833ec9ffe7886ab5ca9fb15d0ae8991dc6d2f` on `test/knowledge-revoked-portal-context-20261108`.
- GitHub PR #1434 remains OPEN; its head was verified as the published commit. PR #1447 remains OPEN and stacked on #1434. No PR was merged and Issue #1350 remains OPEN.
- Exact-head CI was triggered by the push. At the last check, all 23 checks were pending; rerun/refresh before treating CI as complete.
- Published scope was deliberately limited to the 13 Vendor/acceptance/documentation files. Other 81 dirty paths in this worktree belong to other in-progress Agent/Outbox/AssignmentCommand work and remain untouched locally rather than being bundled into this PR.
- PostgreSQL 16 migrations completed on the temporary tmpfs database; the Vendor HTTP acceptance test is committed but not yet verified as passed. The disposable container was removed. No persistent DB, staging service, deployment, or merge was performed.

### GitHub CI follow-up and corrective cleanup - 2026-11-20
- Exact-head CI for documentation publication commit `a43fe9e0925031ee528d61ff895d2482f4c09999` identified three actionable issues: UTF-8 BOM in the new ancestry resolver (production-completeness parser failure), nine redundant f-string prefixes in the API-key contract test (Ruff failure), and `opentelemetry-api==1.45.1` flagged by pip-audit as CVE-2026-126360 (fixed in 1.45.2).
- Corrected the resolver to UTF-8 without BOM; removed the nine redundant f-string prefixes; raised the declared minimum and direct lock pin for `opentelemetry-api` to 1.45.2. No other OpenTelemetry package versions were changed.
- Local revalidation: production completeness baseline **PASS**; focused Vendor resolver/API-key contract suite **34 passed**; targeted Ruff **all checks passed**; Python 3.12 compileall and `git diff --check` passed.
- These fixes are queued for a follow-up commit/push and a fresh exact-head CI run. The previous CI failures are not considered resolved until the new commit's GitHub checks complete successfully.

### OpenTelemetry patch alignment correction - 2026-11-20
- The first dependency-only API bump exposed an exact-version constraint: `opentelemetry-sdk==1.45.1` requires `opentelemetry-api==1.45.1`. The partial lock update therefore failed dependency installation in CI before the audit stage.
- Aligned the three version-coupled direct distributions (`opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`) to **1.45.2** in both `requirements.txt` minimums and `requirements.lock`. Instrumentation package versions remain unchanged.
- Revalidation after alignment: full backend Ruff (`app` + `tests`) passed; focused Vendor resolver/API-key tests **34 passed**; production completeness baseline passed; `git diff --check` passed. Fresh exact-head CI is still required to verify dependency resolution and pip-audit.

### OpenTelemetry instrumentation alignment correction - 2026-11-20
- CI dependency resolution confirmed that OpenTelemetry SDK 1.45.2 requires semantic-conventions 0.66b2, while the pinned FastAPI/SQLAlchemy instrumentation 0.66b1 requires semantic-conventions 0.66b1. The mixed set cannot be installed together.
- Aligned both direct instrumentation packages to **0.66b2** in `requirements.txt` and `requirements.lock`, matching SDK 1.45.2. This follows the exact resolver error; no broad dependency refresh was performed.
- Local static/test checks remain clean. A fresh CI run is required to verify the full lock install and security audit after this final alignment.

### PostgreSQL acceptance test CI isolation correction - 2026-11-20
- The full backend CI run completed **2,033 passed, 1 deselected**, with one failure: the new Vendor PostgreSQL acceptance test raised when its dedicated `LIFECYCLE_TEST_DATABASE_URL` was absent. The test is intentionally local/disposable-database-only and CI does not provision its reserved loopback:15436 database.
- Changed the test's missing-environment behavior to `pytest.skip`; a supplied but non-matching database URL still fails closed. This keeps the live acceptance explicitly gated to the dedicated ephemeral database without failing generic CI or allowing accidental use of staging/shared DBs.
- No live PostgreSQL acceptance is claimed from this correction. Re-run full CI on the new exact head; local Ruff and focused suite are to be revalidated before publication.
