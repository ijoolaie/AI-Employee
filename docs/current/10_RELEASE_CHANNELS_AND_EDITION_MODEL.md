# Release Channels and Edition Model

**Current vendor release:** `v1.2.0`  
**Status date:** 2026-08-24

## Purpose

AI Employee is maintained as one product core, but it is delivered to three distinct commercial roles:

1. **Vendor** — the product owner and primary seller.
2. **Reseller** — a direct customer that is allowed to resell the product.
3. **End Customer** — the reseller's customer who receives an operational deployment.

These roles must be separated without creating permanent code forks.

## Source of truth

`main` is the vendor source of truth. A published vendor release is immutable and is identified by a Git tag and commit SHA.

The certified vendor release covered by the current release evidence is `v1.2.0`. The exact release commit used by a delivery must always be taken from the immutable release tag/workflow evidence, not inferred from a documentation file.

Do not mutate a published release to satisfy a reseller or end-customer requirement. Create a new release instead.

## Three-layer model

```text
Vendor Core Release
        |
        +--> Reseller Edition / Contract Configuration
        |          |
        |          +--> Reseller deployment
        |
        +--> End Customer Deployment Package
                   |
                   +--> Customer tenant(s)
```

The codebase remains shared. Separation is enforced through immutable release references, deployment configuration, tenant boundaries, entitlements, branding, secrets, and delivery manifests.

## Release identity

### Vendor

- Tag: `vMAJOR.MINOR.PATCH`
- Current certified release: `v1.2.0`
- Meaning: canonical product release owned by the vendor.
- Contains: complete certified product core and vendor release evidence.

### Reseller

Reseller deliveries are **not** new product versions. They reference a vendor release plus a reseller contract/configuration revision.

Recommended identifier:

`v1.2.0-reseller.<revision>`

The identifier must resolve to:

- vendor release tag
- vendor commit SHA
- reseller configuration revision
- entitlement set
- deployment target

### End Customer

Customer deliveries reference the reseller delivery and add a customer deployment revision.

Recommended identifier:

`v1.2.0-customer.<revision>`

The identifier must resolve to:

- vendor release tag
- vendor commit SHA
- reseller delivery ID (when applicable)
- customer configuration revision
- entitlement set
- deployment target

## What is separated

| Concern | Vendor | Reseller | End Customer |
|---|---|---|---|
| Product source of truth | Yes | No | No |
| Product release tag | Yes | Referenced | Referenced |
| Code fork | No | No | No |
| Branding | Vendor default | Reseller-specific | Customer-specific |
| Entitlements | Full contract | Contract-specific | Contract-specific |
| Secrets | Vendor-owned | Reseller-owned | Customer-owned |
| Tenant data | Vendor environments | Reseller environments | Customer environments |
| Deployment manifest | Vendor | Reseller | Customer |
| Certification evidence | Product-level | Delivery-level | Deployment-level |
| Upgrade path | Product release | Vendor release + config | Reseller/vendor release + config |

## Security boundary

A delivery package must never contain secrets from another commercial layer. In particular:

- vendor credentials never ship to a reseller or customer;
- reseller credentials never ship to an end customer;
- customer tenant data never becomes part of the vendor source tree or release artifact;
- configuration files contain placeholders or references, not live credentials;
- each deployment has an explicit tenant and environment identity.

## Upgrade rule

An upgrade is represented as a new delivery revision, not an in-place rewrite of an old release.

Example:

`v1.2.0-customer.1` -> `v1.2.1-customer.1`

The customer package must retain the previous manifest so rollback can identify the exact prior immutable vendor release and configuration revision.

## Current v1.2.0 evidence

The v1.2.0 release artifact workflow was executed in GitHub Actions under run `32738347495`. The release certification is recorded in `docs/current/38_V1.2.0_RELEASE_CERTIFICATION_2026-08-24.md`.

## Non-goals

- Do not maintain three long-lived forks of the repository.
- Do not encode customer-specific secrets into Git.
- Do not use Git tags as a substitute for tenant isolation.
- Do not call a customer deployment a vendor release.
