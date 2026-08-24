# Reseller Edition Release Profile

## Identity

The Reseller Edition is a delegated commercial delivery profile referencing an immutable Vendor Edition release.

## Included capabilities

- reseller-scoped administration;
- direct customer provisioning and lifecycle management;
- customer entitlement delegation within vendor-authorized ceilings;
- customer license issuance/revocation;
- reseller support escalation to the vendor;
- reseller branding/configuration;
- reseller release-channel admission.

## Explicit exclusions

The Reseller Edition must not expose vendor-global administration, unrelated reseller/customer data, or arbitrary product-level entitlement authority.

## Required manifest fields

```yaml
edition: reseller
vendor:
  release_tag: <immutable-vendor-release>
  commit_sha: <exact-source-commit>
reseller:
  id: <reseller-id>
  delivery_revision: <reseller-revision>
customer: null
profile:
  name: reseller
  revision: <profile-revision>
  release_channel: reseller
entitlements:
  authority: delegated
  parent_ceiling: <reference>
secrets:
  policy: external-secret-store
  included: false
```

## Rollback

Rollback must identify the previous Vendor release and previous reseller delivery revision. A reseller revision must never mutate an already-delivered revision in place.
