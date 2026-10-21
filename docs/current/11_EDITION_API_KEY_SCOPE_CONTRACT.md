# Commercial Edition API-Key Scope Contract

**Status date:** 2026-10-21
**Implementation status:** local code change; targeted unit and isolated PostgreSQL integration tests passed on 2026-10-21.

## Security contract

Commercial control-plane endpoints retain their existing edition and tenant-boundary checks. API-key scopes are an additional restriction, not a replacement for:

- tenant edition and administrator validation;
- Vendor → Reseller → Customer hierarchy checks;
- license issuer ownership checks;
- support-escalation participant checks;
- entitlement delegation and quota checks.

Bearer-token requests retain the existing edition/RBAC behavior. API-key requests must carry the scope required for the specific endpoint. A superuser API key is still constrained by its explicit scope list. Legacy API keys whose stored `scopes` value is `NULL` are denied access to commercial control-plane endpoints; the dependency identifies API-key authentication by `api_key_id` and never treats a legacy key as bearer authentication.

## Scope families

| Scope | Purpose |
|---|---|
| `edition.vendor.tenants.read` | View vendor hierarchy targets for license management |
| `edition.vendor.resellers.read` | List direct resellers |
| `edition.vendor.resellers.create` | Provision a reseller |
| `edition.vendor.resellers.manage` | Suspend, resume, or deprovision a reseller |
| `edition.reseller.customers.read` | List direct customers |
| `edition.reseller.customers.create` | Provision a customer |
| `edition.reseller.customers.manage` | Suspend, resume, or deprovision a customer |
| `edition.reseller.entitlements.read` | Read direct customer entitlements |
| `edition.reseller.entitlements.delegate` | Delegate an entitlement to a direct customer |
| `edition.licenses.issue` | Issue a commercial license within the issuer's hierarchy |
| `edition.licenses.revoke` | Revoke a license issued by the current tenant |
| `edition.support.read` | Read permitted support escalation lists and messages |
| `edition.support.create` | Create a permitted upward support escalation |
| `edition.support.reply` | Reply to an escalation in which the tenant participates |
| `edition.support.manage` | Change status for an escalation addressed to the tenant |
| `edition.support.attachment.read` | Download an attachment belonging to a participating escalation |

The implementation maintains a tenant-kind allowlist: vendor, reseller, and customer API keys cannot be issued control-plane scopes outside their edition's allowlist. Unknown scope strings are rejected. Ordinary permission scopes continue to be validated against the permission catalog; non-superusers remain limited to permissions held by their tenant roles. Delegating edition control-plane scopes requires a tenant administrator.

## Fail-closed route mapping

The edition dependencies map each protected commercial route (HTTP method + FastAPI route template) to a required scope. If a future endpoint uses an edition dependency but is absent from the mapping, API-key access is denied until the route is deliberately classified. This is intended to make new control-plane endpoints opt-in for API-key access.

## Verification and limitations

- Passed: focused suite `pytest -q tests/test_vendor_internal_billing_exemption.py tests/test_vendor_edition_deps.py tests/test_api_keys.py tests/test_vendor_manual_license_issuance.py` — 17 tests.
- Passed: expanded related backend regression suite covering API keys, edition boundaries, license contracts, feature entitlements, edition profiles and billing contracts — 46 tests.
- Passed: Python compile check for `app/core/edition_deps.py`, `app/api/v1/api_keys.py`, and key new tests.
- Passed: static route inventory audit — all 35 routes in `edition_control.py` and `license_control.py` have scope mappings.
- Passed: `tests/test_commercial_license_postgres_api.py` — 1 PostgreSQL-backed HTTP integration test, executed in a temporary container on the existing isolated Compose network against the dedicated `aiep_license_test` database.
- Passed frontend validation after `npm ci` and after correcting a Persian language-toggle encoding regression found in the final diff review: `npm run lint` (0 errors, 5 warnings), `npm test` (145 frontend contract checks plus governance contract PASS), `npm run test:unit` (80 tests across 15 files), and `npx tsc --noEmit` (0 errors). The unit runner emitted a non-blocking Vite config-loader warning.
- Not run: the entire backend test suite and browser/Playwright E2E. The isolated Compose override was not run alone because it requires the base Compose file; no application services were restarted.
- The PostgreSQL integration test covers API-key creation rejection for unknown and cross-edition scopes, allowed and wrong vendor scopes, a legacy NULL-scope key, a superuser API key with the wrong scope, valid reseller/customer edition scopes, support-message and attachment participant boundaries, and license issue/revocation hierarchy and audit persistence.
- The integration test inserts uniquely named test tenants, users, keys, licenses, and audit entries into the dedicated test database; it does not delete existing records. It does not alter the application's running container or run migrations.
- No commit, push, migration, or production deployment was performed.
- Final diff review found and corrected a Persian language-toggle encoding regression in `frontend/components/layout/sidebar.tsx`; the frontend checks were rerun after the correction.
- Next: consider the entire backend suite only in a separately confirmed safe test environment. Browser/Playwright E2E remains pending.

## Maintenance rule

When adding or changing an endpoint under the commercial edition routers, update the route-to-scope map and the tenant-kind allowlist, add positive and negative tests, and preserve the service-level hierarchy/ownership checks. Do not treat possession of a scope as permission to cross tenant boundaries.
