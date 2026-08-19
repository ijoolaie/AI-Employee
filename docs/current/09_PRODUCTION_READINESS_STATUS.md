# Production Readiness Status

**Status date:** 2026-08-19

## Certified in repository

- Production Certification: PASS
- Product Acceptance: PASS
- Production Hardening: PASS
- PostgreSQL backup/restore smoke: PASS
- Redis persistence/restore smoke: PASS
- Disaster Recovery: PASS
- Production Observability contract: PASS
- Failure detection: PASS
- Rollback contract: PASS
- Notification delivery contract: PASS
- Deployment Readiness: PASS
- Immutable release revision / manifest: PASS
- Production Compose validation: PASS
- Architecture Guard: PASS

The latest deployment-readiness evidence is associated with commit `dcd153d609e5013d30894a638903ea0e63225f53`; the related PR-triggered run set is green.

## Not certified yet

### 1. Live production deployment

Not executed because the repository does not contain a real production target or production credentials. Do not fabricate these values.

Required GitHub Environment (`production`) inputs:

- `PRODUCTION_DEPLOY_HOST`
- `PRODUCTION_DEPLOY_USER`
- `PRODUCTION_DEPLOY_SSH_KEY`
- `PRODUCTION_CONTAINER_REGISTRY`

These must be configured as environment secrets outside the repository.

### 2. External alert provider delivery

The notification contract is tested against a local receiver. External provider delivery (Slack, PagerDuty, or an internal alert gateway) is not certified until `PRODUCTION_ALERT_WEBHOOK_URL` is configured and a real failure produces a successful delivery.

### 3. Live rollback

Rollback is contract-tested but has not been executed against a live production deployment. A live rollback evidence record requires a real deployment target and a successful recovery to the previous immutable revision.

## Recommended final sequence

1. Configure the `production` GitHub Environment and its deployment secrets.
2. Configure `PRODUCTION_ALERT_WEBHOOK_URL`.
3. Run Deployment Readiness against the production environment.
4. Deploy one immutable revision.
5. Verify health/readiness and record deployment evidence.
6. Trigger a controlled rollback drill.
7. Verify recovery and external alert delivery.
8. Mark Live Production and Live Rollback as certified.

## Security rule

No production host, private key, registry credential, webhook secret, or other sensitive infrastructure value belongs in Git history. The repository should remain fail-closed when required production inputs are missing.
