# AI Employee Platform

**Current vendor release:** `v1.1.1`

**Current vendor release position:** `v1.1.1` delivery-hardening patch following immutable vendor release `v1.1.0`.

This repository is the vendor source of truth for the AI Employee Platform. Published vendor releases are immutable snapshots. Reseller and end-customer deliveries reference a vendor release plus their own configuration, entitlement, and deployment revisions; they are not permanent source forks.

## Current release position

**Phase: RELEASE / delivery hardening and handoff preparation**

`v1.1.1` is the current release target on `main`. It records delivery, migration, CI, and documentation hardening completed after the immutable `v1.1.0` vendor release. `v1.0.1` is retained only as a historical rollback reference.

The current `main` revision is the vendor source-of-truth revision for ongoing validation. Production target deployment remains an operational gate until production target secrets are provisioned.

## Delivery model

The product is separated into three commercial layers:

```text
Vendor Core Release
        |
        +--> Reseller Edition / Contract Configuration
        |          |
        |          +--> Reseller deployment
        |
        +--> End Customer Deployment Package
```

Read:

1. `docs/current/10_RELEASE_CHANNELS_AND_EDITION_MODEL.md`
2. `docs/current/11_DELIVERY_PACKAGE_SPEC.md`
3. `docs/current/12_RELEASE_MANIFEST_TEMPLATE.yaml`
4. `docs/releases/v1.1.1.md`

## Release identity

- **Vendor:** `vMAJOR.MINOR.PATCH` — current: `v1.1.1`
- **Reseller delivery:** `v1.1.1-reseller.<revision>`
- **Customer delivery:** `v1.1.1-customer.<revision>`

Reseller/customer identifiers are delivery identities, not replacements for the vendor product version.

## Release and delivery rules

- Keep `main` as the vendor source of truth.
- Never mutate a published release to satisfy one reseller or customer.
- Do not maintain long-lived customer-specific forks.
- Keep secrets and tenant data outside source and release manifests.
- Every handoff must include an immutable manifest linking commercial identity to the exact vendor release SHA.
- Rollback must restore both the previous product revision and the compatible delivery/configuration revision.

## Version alignment

The release version is aligned across the primary application packages:

- Backend: `1.1.1`
- Frontend: `1.1.1`
- Vendor release line: `v1.1.1`

## Existing certification evidence

The repository contains product-level certification and production-readiness evidence. These remain attached to the vendor release and are reused by delivery packages where applicable.

See:

- `docs/current/04_RELEASE_AUDIT.md`
- `docs/current/05_CERTIFICATION_PROGRESS.md`
- `docs/current/09_PRODUCTION_READINESS_STATUS.md`
- `docs/current/RELEASE_POSITION_2026-08-20.md`
- `docs/current/07_CLIENT_HANDOFF_AND_TEST_EVIDENCE.md`
- `docs/releases/v1.1.1.md`

## Migration note

The current Alembic graph must remain authoritative. Run `alembic upgrade head` and `alembic check`; do not stamp the database to conceal a mismatch. The v1.1.1 hardening work includes the migration-head merge required to provide a single upgrade target.
