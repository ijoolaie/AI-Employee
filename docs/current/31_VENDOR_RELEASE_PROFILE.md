# Vendor Edition Release Profile

## Identity

The Vendor Edition is the canonical commercial authority. It is produced from an immutable vendor source release and carries the complete product-level evidence set.

## Included capabilities

- vendor control-plane administration;
- direct reseller provisioning and lifecycle management;
- product/package authority;
- commercial license issuance and revocation for downstream editions;
- entitlement authority and quota ceilings;
- release authority and supported-version policy;
- provider/global configuration management;
- vendor audit and support escalation authority.

## Explicit exclusions

The Vendor Edition must not be configured as a customer-only deployment and must not delegate its global authority to downstream tenants.

## Required manifest fields

```yaml
edition: vendor
vendor:
  release_tag: <immutable-vendor-release>
  commit_sha: <exact-source-commit>
reseller: null
customer: null
profile:
  name: vendor
  revision: <profile-revision>
  release_channel: vendor
entitlements:
  authority: product
secrets:
  policy: external-secret-store
  included: false
```

## Rollback

Vendor rollback identifies the previous immutable vendor release and its verified artifact digest. Profile revision changes do not silently replace an existing vendor release.
