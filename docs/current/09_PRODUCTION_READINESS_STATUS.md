# Production Readiness Status

**Status date:** 2026-08-24

## Repository and local production-like status

The repository-level certification and productization implementation remain distinct from external production certification.

Current local evidence includes:

- Backend suite: **238 passed** on 2026-08-23.
- Production-like Docker API: healthy.
- Production-like frontend: healthy.
- PostgreSQL: healthy.
- Redis: healthy.
- API dependency readiness: PASS.
- Frontend `/login`: PASS.
- PostgreSQL logical restore + Redis AOF restore smoke: PASS.
- Controlled API recovery drill: PASS.
- Release artifact workflow includes exact-release checkout, package build, checksum verification and release notes generation from the exact release ref.

The latest local recovery drill recorded known-good revision:

`fc214360715d194c5057de2da341f0768298751d`

This is valid local production-like evidence only. It is not evidence of an external customer-facing production host.

## Production environment preparation

The repository now contains:

- `docs/current/28_PRODUCTION_ENVIRONMENT_PREPARATION.md` — required target inputs, release admission, deployment sequence and recovery preparation.
- `docs/current/29_COMMERCIAL_SUPPORT_UPDATE_POLICY.md` — commercial support responsibilities, escalation and update/change-control policy.

These contracts make the external deployment path executable once a real target exists without placing secrets or infrastructure credentials in Git history.

## External live environment — NOT YET CERTIFIED

### 1. Live production deployment

Not executed because a real external production target and production credentials are not part of the repository. Do not fabricate these values.

When a real target exists, configure a protected GitHub `production` Environment and provide deployment credentials through the platform secret manager. Expected secret names are deployment-specific; do not commit them to Git.

### 2. External monitoring and alert delivery

Repository/local observability contracts are implemented. External monitoring and alert delivery require a real configured provider and successful real failure notification evidence.

### 3. External backup/restore and rollback

Local backup/restore and recovery are PASS. Target-environment rehearsal remains required for production certification.

### 4. Commercial payment and revenue

Live payment/webhook processing and real subscriber/revenue evidence remain open commercial exit gates.

### 5. Final production security certification

Security configuration and secret controls are implemented and locally validated where applicable. Final certification remains target-specific and must be performed against the actual deployment.

## Required production sequence

1. Create/verify the immutable release tag and release artifact.
2. Run the release artifact workflow in GitHub Actions when Actions capacity is available.
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

## Security rule

No production host, private key, registry credential, webhook secret, payment secret, customer data or environment-specific access token belongs in Git history. Missing required production inputs must fail closed.
