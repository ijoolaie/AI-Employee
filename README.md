# AI Employee Platform

**Current vendor release:** `v1.2.0`

**Current vendor release position:** `v1.2.0` certified controlled-deployment release; V1.4 dependency-ordered gap closure is in progress.

This repository is the vendor source of truth for the AI Employee Platform. Published vendor releases are immutable snapshots. Reseller and end-customer deliveries reference a vendor release plus their own configuration, entitlement, and deployment revisions; they are not permanent source forks.

## Current release position

**Phase: PRODUCTIZATION / V1.4 GAP CLOSURE + PHASE 6E EXTERNAL DELIVERY PREPARATION**

`v1.2.0` is the current certified controlled-deployment vendor release. The V1.4 architecture baseline is frozen and the first dependency-ordered implementation wave (#69–#73) is complete, with #73 merged and verified. Phase 6E remains an external-production gate and is not certified until real target evidence exists.

The current `main` revision is the vendor source-of-truth revision for ongoing validation. Production target deployment remains an operational gate until target-specific secrets, infrastructure and acceptance evidence are provisioned.

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
4. `docs/current/38_V1.2.0_RELEASE_CERTIFICATION_2026-08-24.md`
5. `docs/current/40_GITHUB_MAIN_VERIFICATION_2026-08-26.md`

## Release identity

- **Vendor:** `vMAJOR.MINOR.PATCH` — current: `v1.2.0`
- **Reseller delivery:** `v1.2.0-reseller.<revision>`
- **Customer delivery:** `v1.2.0-customer.<revision>`

Reseller/customer identifiers are delivery identities, not replacements for the vendor product version.

## V1.4 implementation checkpoint

The first dependency-ordered V1.4 gap-closure wave is complete:

```text
#69  Tenant / Worker Context              ✅
#70  Knowledge Tenant Isolation           ✅
#71  Conversation Tenant Isolation        ✅
#72  Scoped API Keys                      ✅
#73  Idempotent Usage Event Ledger        ✅ MERGED
```

PR #73 merged into `main` at commit `df82a3c69c50e4d711ee1c61887c8c8fdf0beb35`. The merged implementation adds a durable tenant-scoped usage-event ledger with unique `(tenant_id, event_key)` identity and idempotent recording.

## Release and delivery rules

- Keep `main` as the vendor source of truth.
- Never mutate a published release to satisfy one reseller or customer.
- Do not maintain long-lived customer-specific forks.
- Keep secrets and tenant data outside source and release manifests.
- Every handoff must include an immutable manifest linking commercial identity to the exact vendor release SHA.
- Rollback must restore both the previous product revision and the compatible delivery/configuration revision.

## Existing certification evidence

The repository contains product-level certification and production-readiness evidence. These remain attached to the vendor release and are reused by delivery packages where applicable.

See:

- `docs/current/09_PRODUCTION_READINESS_STATUS.md`
- `docs/current/38_V1.2.0_RELEASE_CERTIFICATION_2026-08-24.md`
- `docs/current/40_GITHUB_MAIN_VERIFICATION_2026-08-26.md`
- `docs/current/PRODUCTIZATION_ROADMAP.md`
- `docs/current/07_CLIENT_HANDOFF_AND_TEST_EVIDENCE.md`

## Public repository preparation

Before repository visibility is changed to public, run:

```bash
python scripts/public_repository_audit.py
```

The audit checks the current tracked tree, reachable Git history and GitHub Actions workflow files for common secret/token exposure patterns and flags temporary branches for manual review.

See `docs/current/37_PUBLIC_REPOSITORY_READINESS_2026-08-24.md` for the publication gate. Public visibility is intentionally separate from production certification and does not imply that external production evidence exists.

Security reporting guidance is in `SECURITY.md`.

## License

No explicit open-source license is declared yet. Public visibility alone does not grant reuse rights. Choose and publish the intended license before treating the repository as an open-source project.

## Migration note

The current Alembic graph must remain authoritative. Run `alembic upgrade head` and `alembic check`; do not stamp the database to conceal a mismatch. The V1.4-005 implementation adds migration `v14005usage` on top of the frozen migration graph.
