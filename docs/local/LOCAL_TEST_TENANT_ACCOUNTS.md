# Local Test Tenant Accounts and License Renewal

> **Scope:** isolated local development/test environment only. This is an operator runbook, not a production onboarding guide.
>
> **Secrets:** passwords are chosen locally and must never be committed here. This repository is public.

## Canonical local environment

For the isolated `AI-Employee-main-sync` checkout:

- Frontend: `http://localhost:13010`
- API base: `http://localhost:18010/api/v1`
- OpenAPI/Swagger: `http://localhost:18010/docs`

If you are testing the primary checkout instead, use its currently configured ports and verify them with Docker Compose first. Do not point this runbook at a production API.

## Test identities

Use these stable identifiers to avoid inventing new tenants for every test. A tenant slug is part of login and is not a password.

| Role | Tenant name | Tenant slug | Admin email | Current handling |
|---|---|---|---|---|
| Vendor | Raya Local Vendor | `raya-local-vendor` | `raya.vendor@example.test` | Existing local vendor tenant; reuse it. Do not recreate, delete, or alter its role/entitlements as part of routine tests. |
| Reseller | Raya Local Reseller | `raya-local-reseller` | `raya.reseller@example.test` | Reuse if present; otherwise create from the vendor panel. |
| Customer | Raya Local Customer | `raya-local-customer` | `raya.customer@example.test` | Reuse if present; otherwise create from the reseller panel. |

The `.test` domain is reserved for test use. These addresses are not intended to receive email. The repository intentionally does not store passwords. If a password is unknown, use the supported password-reset/admin process available in the local environment; do not read or overwrite password hashes directly in the database.

Expected hierarchy:

```text
Raya Local Vendor (vendor)
└── Raya Local Reseller (reseller)
    └── Raya Local Customer (customer)
```

## Create or reuse the accounts

### 1. Vendor administrator

1. Start the isolated local stack and open the frontend URL above.
2. Sign in using tenant slug `raya-local-vendor`, email `raya.vendor@example.test`, and the locally chosen password.
3. If this account does not exist or cannot authenticate, stop and use the project's approved vendor bootstrap/provisioning procedure. Ordinary public registration creates a regular tenant; it must not be used as a shortcut to grant vendor/platform-admin authority.
4. Do not elevate a customer/reseller account or edit database rows manually to make it a vendor.

### 2. Create the reseller from the Vendor panel

1. While signed in as the vendor administrator, open **Admin → Resellers** (route `/admin/resellers`).
2. In the create form enter:
   - Name: `Raya Local Reseller`
   - Slug: `raya-local-reseller`
   - Admin email: `raya.reseller@example.test`
   - Admin password: a unique local-only password of at least 12 characters
   - Full name: `Local Reseller Admin` (optional)
3. Submit once. If the slug already exists, do not create a second tenant: inspect the reseller list and reuse the existing tenant.
4. Sign out and sign in with tenant slug `raya-local-reseller` and the reseller admin credentials.

The corresponding API operation is `POST /api/v1/edition/vendor/resellers`. It is vendor-admin scoped and expects `name`, `slug`, `admin_email`, `admin_password`, and optional `full_name`.

### 3. Create the customer from the Reseller panel

1. While signed in as the reseller administrator, open **Reseller → Clients** (route `/reseller/clients`).
2. Enter:
   - Name: `Raya Local Customer`
   - Slug: `raya-local-customer`
   - Admin email: `raya.customer@example.test`
   - Admin password: a unique local-only password of at least 12 characters
   - Full name: `Local Customer Admin` (optional)
3. Submit once. If the slug already exists, reuse the existing customer rather than creating a duplicate.
4. Sign out and sign in with tenant slug `raya-local-customer` and the customer admin credentials.

The corresponding API operation is `POST /api/v1/edition/reseller/customers`. It is reseller-admin scoped and creates a direct child customer tenant.

### 4. Verify login and tenant boundaries

- Log in separately to all three accounts using the matching tenant slug and email.
- Confirm the vendor can see its direct reseller, the reseller can see its direct customer, and the customer cannot provision downstream tenants.
- Confirm one tenant cannot access another tenant's private records by changing IDs or API paths.
- Record a tenant as **verified** only after login and its expected access boundaries have been tested.

Do not manually insert partial Tenant/User rows into PostgreSQL. The supported provisioning operations establish parent-child links, tenant kind, admin account, and required invariants.

## Issue or renew a test license

A successful login does not mean a customer can run an Employee. Run creation/execution can be blocked by a missing, expired, revoked, or insufficiently scoped commercial license.

**Renewal means issuing a new license.** The current API exposes issue and revoke operations, not an in-place expiry extension. Keep the old license record for audit history; do not edit `expires_at` in the database.

Open Swagger at `http://localhost:18010/docs` and use the endpoints below while authenticated as the appropriate administrator:

| Issuer | Operation | Endpoint |
|---|---|---|
| Vendor admin | Issue/renew the reseller license | `POST /api/v1/edition/licenses/vendor/resellers/{reseller_id}` |
| Reseller admin | Issue/renew the customer license | `POST /api/v1/edition/licenses/reseller/customers/{customer_id}` |

Use the tenant UUID returned by the provision/list API for `{reseller_id}` or `{customer_id}`; do not guess IDs. The request body schema is `LicenseIssueRequest`:

```json
{
  "expires_in_days": 30,
  "feature_codes": ["employee.run"],
  "metadata": {
    "purpose": "local-test",
    "renewal": true
  }
}
```

- `expires_in_days` is optional, from 1 to 3650. Set it explicitly for repeatable tests.
- `feature_codes` must contain the features required by the test. For a tool-enabled Run, include the exact required tool entitlement as well (for example, `tool:workforce_keyword_research`) in addition to `employee.run`. Do not grant unrelated features just to make a test pass.
- `metadata` is optional and should contain only non-secret test notes.
- The response contains the new license ID, status, issue time, expiry time, and feature codes. Save the license ID/expiry in the local test notes, not credentials.
- Vendor licenses are issued by the vendor to direct reseller children; customer licenses are issued by the reseller to direct customer children. A customer cannot issue or renew its own license.
- If a license is revoked, issue a new license only if the test scenario requires it and the authorized issuer approves. Never silently bypass entitlement checks.

If a request fails, inspect the response and the Swagger schema. Do not guess alternative payload fields or manually modify license tables.

## Repeatable pre-test checklist

- [ ] Isolated API and database are healthy.
- [ ] Vendor, reseller, and customer tenants are reused by slug; no duplicate tenants created.
- [ ] Correct tenant slug/email/password combination can log in.
- [ ] Customer has an active, non-expired license from its parent reseller.
- [ ] License includes the exact feature/tool codes required by the test.
- [ ] Worker/Beat and configured provider are running when the scenario needs them.
- [ ] Test result is read back through the API/UI and tenant boundaries remain intact.

## Cleanup and safety

These are disposable local test identities, but preserve the stable vendor account used by other local workflows. Use supported deprovision/cleanup controls for child tenants only when cleanup is actually needed. Removing a row manually or deleting this document does not clean the database. Never reuse local test passwords in production, and never store passwords, tokens, session cookies, or production credentials in Git.
