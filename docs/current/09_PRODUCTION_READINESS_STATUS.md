# Production Readiness Status

**Status date:** 2026-08-26

## Current release and project boundary

The current certified controlled-deployment vendor release is **v1.2.0**. Release artifact certification is recorded in `docs/current/38_V1.2.0_RELEASE_CERTIFICATION_2026-08-24.md`.

The V1.4 architecture baseline is frozen, and dependency-ordered V1.4 gap closure is now in progress. PRs #69–#73 completed the first implementation wave; PR #73 was merged after its CI/test correction.

Repository implementation and CI/release verification remain distinct from external production certification.

## Current evidence layers

### Repository / implementation evidence

The first V1.4 gap-closure wave is complete through PR #73:

- Tenant / worker context: complete.
- Knowledge tenant isolation: complete.
- Conversation tenant isolation: complete.
- Scoped API keys: complete.
- Idempotent usage event ledger: merged in PR #73.

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

This is valid local production-like evidence only. It is not evidence of an external customer-facing production host.

### Release / CI evidence

The v1.2.0 release workflow was successfully executed in GitHub Actions under run `32738347495`, producing the runtime and edition artifacts recorded in the release certification document.

PR #73 also completed its required verification workflow after the test import correction and was merged. CI/CodeQL/architecture/observability/rollback verification must continue to be treated as repository evidence, not production deployment evidence.

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

The 2026-08-26 documentation snapshot is the reconciliation point before the next implementation wave. Older/open planning PRs must be reconciled against the frozen V1.4 baseline and the already-completed #69–#73 execution chain before they are treated as authoritative work items.

## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history. Missing required production inputs must fail closed.
