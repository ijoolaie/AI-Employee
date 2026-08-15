# Production Release Runbook

## Pre-release

- [ ] Freeze feature changes.
- [ ] Confirm migration backup.
- [ ] Confirm secrets are loaded from the secret manager.
- [ ] Apply database migrations.
- [ ] Confirm API dependency health.
- [ ] Confirm worker/beat processes are healthy.
- [ ] Confirm frontend build artifact.
- [ ] Confirm TLS certificate and DNS.

## Rollout

1. Deploy API/worker/beat.
2. Wait for health/readiness.
3. Deploy frontend.
4. Smoke-check login, dashboard and one authenticated API call.
5. Enable traffic gradually if supported.

## Rollback

- Stop new application traffic.
- Revert application image to previous immutable version.
- Do not automatically downgrade the database schema.
- If a migration is backward-incompatible, follow the migration-specific rollback procedure.
- Restore data only when an approved recovery decision has been made.

## Incident response

Capture timestamp, release ID, affected tenant(s), correlation/request IDs, provider status, queue depth, database health and recent deploys. Preserve logs before remediation.
