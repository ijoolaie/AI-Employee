# Customer Edition Release Profile

## Identity

The Customer Edition is the end-customer deployment profile. It references an immutable Vendor Edition release and, where applicable, a Reseller delivery revision.

## Included capabilities

- isolated customer operations;
- customer-scoped employees, runs, files, workflows and data;
- customer configuration and branding;
- customer license and entitlement consumption;
- upgrade/recovery surface defined by the supported release channel;
- support escalation to the direct reseller or vendor.

## Explicit exclusions

The Customer Edition must not provision sibling customers, issue downstream licenses, delegate reseller entitlements, or access vendor/global control-plane functions.

## Required manifest fields

```yaml
edition: customer
vendor:
  release_tag: <immutable-vendor-release>
  commit_sha: <exact-source-commit>
reseller:
  id: <reseller-id-or-null>
  delivery_revision: <reseller-revision-or-null>
customer:
  id: <customer-id>
  deployment_revision: <customer-revision>
profile:
  name: customer
  revision: <profile-revision>
  release_channel: customer
entitlements:
  authority: consumed
secrets:
  policy: customer-secret-store
  included: false
```

## Rollback

Rollback must identify both the previous immutable Vendor release and the previous customer deployment revision. Restoring only container images is insufficient when configuration or migration state is newer.
