# AI Employee Platform

**Current implementation baseline:** `V1.4 ACTIVE EXECUTION BASELINE`

**Latest certified vendor release:** `v1.2.0` — certified controlled-deployment release. V1.4 dependency-ordered gap closure is actively in progress and is already partially implemented.

This repository is the vendor source of truth for the AI Employee Platform. Published vendor releases are immutable snapshots. Reseller and end-customer deliveries reference a vendor release plus their own configuration, entitlement, and deployment revisions; they are not permanent source forks.

## Current project position

**Phase: PRODUCTIZATION / V1.4 GAP CLOSURE + PHASE 6E EXTERNAL DELIVERY PREPARATION**

The current `main` implementation baseline is **V1.4**. The V1.4 architecture baseline is frozen and the first dependency-ordered implementation wave (#69–#73) is complete, with #73 merged and verified. PR #77 subsequently reconciled the remaining Alembic heads on `main`. Phase 6E remains an external-production gate and is not certified until real target evidence exists.

The latest certified vendor release remains `v1.2.0`; this is a release identity, not the current implementation-version label for `main`.

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
6. `docs/current/V1.4_EXECUTION_STATUS_2026-08-26.md`
7. `docs/current/V1.4_DOCUMENTATION_RECONCILIATION_2026-08-26.md`

## Release identity

- **Current implementation baseline:** `V1.4`
- **Latest certified vendor release:** `v1.2.0`
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

PR #73 was merged after its CI/test correction. The current repository baseline then advanced through the documentation reconciliation and Alembic-head merge work, including PR #77.

## Release and delivery rules

- Keep `main` as the vendor source of truth.
- Never mutate a published release to satisfy one reseller or customer.
- Do not maintain long-lived customer-specific forks.
- Keep secrets and tenant data outside source and release manifests.
- Every handoff must include an immutable manifest linking commercial identity to the exact vendor release SHA.
- Rollback must restore both the previous product revision and the compatible delivery/configuration revision.

## Existing certification evidence

The repository contains product-level certification and production-readiness evidence. These remain attached to the certified vendor release and are reused by delivery packages where applicable.

See:

- `docs/current/09_PRODUCTION_READINESS_STATUS.md`
- `docs/current/38_V1.2.0_RELEASE_CERTIFICATION_2026-08-24.md`
- `docs/current/40_GITHUB_MAIN_VERIFICATION_2026-08-26.md`
- `docs/current/V1.4_EXECUTION_STATUS_2026-08-26.md`
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

The current Alembic graph must remain authoritative. Run `alembic upgrade head` and `alembic check`; do not stamp the database to conceal a mismatch. The V1.4-005 implementation adds migration `v14005usage`, and PR #77 reconciles the remaining Alembic heads on `main`.
