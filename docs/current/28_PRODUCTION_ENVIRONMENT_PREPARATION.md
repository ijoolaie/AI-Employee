# Production Environment Preparation Contract

**Status date:** 2026-08-24
**Scope:** preparation only; this document does not claim a live production deployment.

## Purpose

Define the exact inputs and verification steps required before using a real production target. The repository remains safe and reproducible when the production target is unavailable.

## Required production inputs

The target deployment operator must provide these outside Git history:

- Production deployment host or managed deployment target.
- Deployment identity and least-privilege access method.
- Immutable container image source or release artifact location.
- Production database endpoint and credentials.
- Production Redis endpoint and credentials.
- Celery broker/result endpoints where applicable.
- Secret-manager values for `SECRET_KEY` and all enabled integration credentials.
- HTTPS domain and trusted-origin configuration.
- Persistent application-storage destination and backup destination.
- Monitoring/logging destination and alert delivery endpoint.

## Optional external integrations

Enable only what the customer contract requires:

- Stripe payment provider and webhook signing secret.
- Shopify credentials and webhook configuration.
- SMTP provider and recipient-domain allowlist.
- LM Studio or other configured AI provider.
- Object storage provider.

An omitted optional integration must remain fail-closed rather than silently using repository defaults.

## Release admission

Before deployment, record:

1. Exact immutable release tag/commit.
2. Release manifest and SHA-256 checksums.
3. Migration head.
4. Supported channel and target version.
5. Current target version for upgrades.
6. Backup identifier created immediately before migration.
7. Rollback target and its artifact/checksum.

The target release must pass the supported-version policy before upgrade. Downgrades are handled through the rollback workflow, not the upgrade path.

## Deployment sequence

1. Provision production secrets through the approved secret manager.
2. Validate configuration without exposing secret values in logs.
3. Verify HTTPS/reverse-proxy and trusted-origin configuration.
4. Verify database, Redis and queue connectivity from the deployment target.
5. Create and verify the pre-deployment backup.
6. Deploy the immutable artifact.
7. Run migrations and record the before/after heads.
8. Verify API liveness and dependency readiness.
9. Verify worker/beat health and queue processing.
10. Verify frontend/customer entry points.
11. Verify monitoring and external alert delivery.
12. Run customer acceptance smoke tests.
13. Record the release, operator, environment and evidence references.

## Recovery preparation

A target is not ready for commercial handoff until these are known before rollout:

- Previous known-good artifact.
- Previous supported version.
- Latest verified backup.
- Restoration procedure and target location.
- Rollback owner and escalation contact.
- Recovery acceptance checks.

## Evidence boundary

Local Docker evidence proves repository deployment/recovery behavior only. It must not be reclassified as external production evidence. Production certification requires fresh evidence from the actual deployment target.

## Security rule

Never commit production secrets, private keys, provider credentials, customer data, or environment-specific access tokens. Missing required production inputs must fail closed.
