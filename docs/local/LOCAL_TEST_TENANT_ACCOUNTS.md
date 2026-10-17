# Local Test Tenant Accounts

> **Environment:** local development only  
> **Provisioning status:** planned — these accounts have not yet been created or login-tested.  
> **Passwords:** intentionally not stored in this repository. Set a unique local-only password for each account when provisioning it.

This repository is public. Do not add passwords, tokens, session cookies, production credentials, or other secrets to this file or to Git history.

## Planned test accounts

| Tenant kind | Tenant name | Tenant slug | Admin email | Admin display name | Status |
|---|---|---|---|---|---|
| Vendor | Raya Local Vendor | `raya-local-vendor` | `raya.vendor@example.test` | Local Vendor Admin | Not created / not verified |
| Reseller | Raya Local Reseller | `raya-local-reseller` | `raya.reseller@example.test` | Local Reseller Admin | Not created / not verified |
| Customer | Raya Local Customer | `raya-local-customer` | `raya.customer@example.test` | Local Customer Admin | Not created / not verified |

The `.test` email domain is reserved for testing; these addresses are not intended to receive email.

## Intended tenant hierarchy

```text
Raya Local Vendor (vendor)
└── Raya Local Reseller (reseller)
    └── Raya Local Customer (customer)
```

Reseller and customer tenants must be provisioned through the supported edition-control flow so that parent-child boundaries, tenant kind, admin role, and permissions are configured correctly. Do not create these records by manually inserting partial rows into the database.

## Local setup and verification checklist

- [ ] Confirm the local API and database are running.
- [ ] Create the vendor tenant and its admin using the supported registration/provisioning path.
- [ ] Sign in as the vendor admin and create the reseller under that vendor.
- [ ] Sign in as the reseller admin and create the customer under that reseller.
- [ ] Verify each account can sign in with its own tenant slug and chosen password.
- [ ] Verify tenant isolation and the customer/reseller support routes.
- [ ] Update the status column only after each account has been created and login-tested.

## Before any external deployment

These are disposable local test tenants. Before external testing or deployment, remove them from the local test database using the project's supported cleanup process, or recreate a clean database. Do not rely on deleting this documentation or a Git commit to remove database records. Rotate any credentials that may have been exposed and never reuse local test passwords in another environment.
