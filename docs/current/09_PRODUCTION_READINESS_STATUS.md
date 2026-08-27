# Production Readiness Status

**Status date:** 2026-08-26

## Current release and project boundary

The current certified controlled-deployment vendor release is **v1.2.0**. Release artifact certification is recorded in `docs/current/38_V1.2.0_RELEASE_CERTIFICATION_2026-08-24.md`.

The V1.4 architecture baseline is frozen, and dependency-ordered V1.4 gap closure is now in progress. PRs #69–#73 completed the first implementation wave; PR #73 was merged after its CI/test correction.

Phase 7 Invoice Employee is already implemented in the repository as v0.7.0 with the v0.7.1 tax-rate amendment and a local real-model E2E verification record. This is repository/local evidence, not external production certification.

Repository implementation and CI/release verification remain distinct from external production certification.

## Current evidence layers

### Repository / implementation evidence

The first V1.4 gap-closure wave is complete through PR #73:

- Tenant / worker context: complete.
- Knowledge tenant isolation: complete.
- Conversation tenant isolation: complete.
- Scoped API keys: complete.
- Idempotent usage event ledger: merged in PR #73.

Phase 7 evidence:

- Invoice Employee v0.7.0 implementation: present.
- v0.7.1 tax-rate normalization amendment: present.
- Unit/service verification: present in repository.
- Local real-model E2E verification record: present.
- External production acceptance: not recorded.

### Local production-like evidence

Current local evidence includes:

- Backend suite previously recorded at 238 passed on 2026-08-23.
- Production-like Docker API: healthy.
- Production-like frontend: healthy.
- PostgreSQL: healthy.
- Redis: healthy.
- API dependency readiness: PASS.
- Frontend `/login`: PASS.
- PostgreSQL logical restore + Redis AOF restore smoke: PASS.
- Controlled API recovery drill: PASS.
- Phase 7 real-model E2E: recorded as local verification in `docs/current/RELEASE_VERIFICATION_v0.7.1.md`.

This is valid local production-like evidence only. It is not evidence of an external customer-facing production host.

### Release / CI evidence

The v1.2.0 release workflow was successfully executed in GitHub Actions under run `32738347495`, producing the runtime and edition artifacts recorded in the release certification document.

PR #73 also completed its required verification workflow after the test import correction and was merged. CI/CodeQL/architecture/observability/rollback verification must continue to be treated as repository evidence, not production deployment evidence.

## GitHub PR governance reconciliation — 2026-08-26

The older open PR queue has been reconciled against the frozen V1.4 baseline and the completed #69–#73 implementation wave:

- **#73:** merged and verified; usage-event idempotency gap closed.
- **#69–#72:** completed first V1.4 implementation wave.
- **#67:** closed without merge; superseded planning document. Its execution-plan content is represented by the current V1.4 baseline/roadmap.
- **#68:** closed without merge; superseded baseline-audit document. Its conclusions are represented by the current documentation baseline.
- **#64:** closed without merge; stale draft v1.3.1 foundation branch and no longer the active execution frontier.
- **#57:** closed without merge; Shopify external-certification preparation retained as a target-specific/future activity rather than an active blocking PR.

Closing these PRs is repository governance/bookkeeping. It does not certify any external environment and does not mark the associated external gates complete.

## Phase 7 — Invoice Employee

**Status: 🟢 IMPLEMENTED / LOCAL VERIFIED; EXTERNAL PRODUCTION ACCEPTANCE OPEN.**

The locked scope in `documents/66_PHASE_7_INVOICE_EMPLOYEE_SCOPE_LOCK_v0.7.0.md` is implemented. The repository contains invoice creation, line items/tax/currency/due date, ingest/analysis, status tracking, tenant-scoped outstanding/collected summaries, PDF export, and the v0.7.1 tax-rate normalization amendment.

`docs/current/RELEASE_VERIFICATION_v0.7.1.md` records local real-model E2E verification. It must not be interpreted as external production evidence. No duplicate Phase 7 implementation PR should be created unless a new, demonstrated gap is found.

## External live environment — NOT YET CERTIFIED

### 1. Live production deployment

Not yet certified. A real external production target and production credentials are required; do not fabricate these values.

### 2. External monitoring and alert delivery

Repository/local observability contracts are implemented. External monitoring and alert delivery require a real configured provider and successful real failure-notification evidence.

### 3. External backup/restore and rollback

Local backup/restore and recovery are PASS. Target-environment rehearsal remains required for production certification.

### 4. Commercial payment and revenue

Live payment/webhook processing and real subscriber/revenue evidence remain open commercial exit gates.

### 5. Final production security certification

Security configuration and secret controls are implemented and locally validated where applicable. Final certification remains target-specific and must be performed against the actual deployment.

## Phase 6E evidence boundary

Phase 6E is **READY FOR EXTERNAL EXECUTION**, not complete.

Mandatory delivery order:

1. Vendor environment.
2. Reseller environment.
3. Customer environment.

For each real environment, capture installation/health, migration state, security posture, monitoring/alerting, backup/recovery, edition-specific authority boundaries, and operator handoff/acceptance.

The current `docs/evidence/phase6e/` Vendor, Reseller and Customer records are evidence templates/contracts until populated with real environment-specific evidence. They must not be interpreted as production acceptance.

## Required production sequence

1. Create/verify the immutable release tag and release artifact.
2. Run the release artifact workflow in GitHub Actions.
3. Provision target secrets through the approved secret manager.
4. Configure HTTPS, trusted origins and target infrastructure endpoints.
5. Deploy API, worker, Beat and frontend as applicable.
6. Verify liveness/readiness, queue health and persistent storage.
7. Verify external monitoring/alerting.
8. Verify enabled external integrations and payment/webhook signatures.
9. Execute target backup/restore and rollback/recovery rehearsal.
10. Execute real commercial payment/subscriber verification.
11. Run final customer acceptance and security certification.
12. Record the production evidence and release classification.

## Documentation / governance checkpoint

**2026-08-26 reconciliation checkpoint: UPDATED.** The roadmap and production-readiness status now reflect the current repository evidence: #69–#73 form the completed first V1.4 implementation wave, #73 is merged, stale/superseded PRs #57, #64, #67 and #68 are closed without merge, and Phase 7 Invoice Employee is already implemented and locally verified through v0.7.1.

## Next execution frontier

Two tracks are explicit and may proceed independently while preserving their evidence boundaries:

1. **V1.4 gap closure:** continue the next dependency-ordered implementation slice from the frozen Blueprint. Each slice requires its own tests/CI and documentation update. Do not reimplement existing Billing/Payment or Phase 7 capabilities without a demonstrated gap.
2. **Phase 6E external delivery:** execute Vendor → Reseller → Customer against real infrastructure and populate the Phase 6E evidence records. 6E remains incomplete until its required environment-specific evidence and acceptance gates are satisfied.

## Version and release namespace reconciliation — 2026-08-27

The repository distinguishes product releases, architecture baselines, execution waves and documentation-package revisions. The authoritative reconciliation is recorded in `docs/current/44_VERSION_RELEASE_RECONCILIATION_2026-08-27.md`.

- **v1.2.0:** current certified controlled-deployment product release.
- **v1.3.0:** historical/unreconciled release claim; it does not override current v1.2.0 release truth without immutable release evidence reconciliation.
- **V1.4:** frozen architecture baseline with active implementation; it is not currently equivalent to a released `v1.4.0` product version.


## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history. Missing required production inputs must fail closed.
