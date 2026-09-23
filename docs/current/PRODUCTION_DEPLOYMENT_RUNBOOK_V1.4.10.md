# v1.4.10 Production Deployment Runbook

**Status:** READY FOR EXTERNAL EXECUTION  
**Release:** `v1.4.10`  
**Certified SHA:** `b09f3e35d512e3c4d21be9d930539cbbe1d2d451`  
**Production Certification:** run `35840044046` / job `107112696112` — PASS  
**Stable tag:** `v1.4.10` — VERIFIED  
**GitHub Release:** `v1.4.10` — PUBLISHED

> This runbook is an execution guide. It does not claim that production has been deployed.

## 1. Admission gate

Before touching the target:

1. Verify tag `v1.4.10` resolves exactly to `b09f3e35d512e3c4d21be9d930539cbbe1d2d451`.
2. Record the current deployed release and migration head.
3. Verify the previous known-good release and rollback artifact.
4. Create and independently verify a fresh PostgreSQL backup.
5. Confirm backup storage is outside the primary failure domain.
6. Confirm DNS/TLS/firewall/SSH access.
7. Confirm required secrets exist without printing values.
8. Confirm monitoring and alert delivery are reachable.

**Hard stop:** do not migrate if backup, rollback, or required target credentials are unavailable.

## 2. Deployment workflow

The repository provides `.github/workflows/production-deploy-target.yml` as a manually dispatched target deployment gate. It requires:

- `PRODUCTION_DEPLOY_HOST`
- `PRODUCTION_DEPLOY_USER`
- `PRODUCTION_DEPLOY_SSH_KEY`
- `PRODUCTION_CONTAINER_REGISTRY`

These values must come from the real target environment. Never fabricate them for testing.

## 3. Production topology

The production Compose topology contains PostgreSQL 16, Redis 7, API, Celery worker, Celery Beat, storage-init and Next.js frontend.

Public TLS/DNS/firewall/ingress are external target responsibilities. PostgreSQL and Redis must remain private.

## 4. Post-deploy verification

Verify:

- PostgreSQL healthy
- Redis healthy
- API `/health/dependencies` healthy
- frontend login reachable
- worker and Beat running
- migration graph has a single head
- no startup configuration/secret errors
- HTTPS certificate and hostname correctness
- authenticated API request
- controlled background job
- configured provider smoke test
- audit event generation
- tenant/RBAC negative path

## 5. Backup/restore

Use the repository backup and restore scripts. Restore only into an isolated recovery database during validation.

Record:

- backup timestamp/size/checksum
- restore start/end
- migration head
- representative integrity checks
- measured RPO
- measured RTO

Engineering targets are RPO <= 15 minutes and RTO <= 60 minutes; these become production evidence only when measured on the target.

## 6. Rollback

If release health/readiness fails:

1. Stop the rollout.
2. Preserve logs and deployment metadata.
3. Identify the previous known-good immutable release.
4. Verify its artifact/image digest.
5. Redeploy the known-good revision.
6. Re-run readiness and critical smoke checks.
7. Record the incident and rollback result.

Do not rewrite or retag `v1.4.10`.

## 7. External acceptance

Acceptance is sequential:

**Vendor → Reseller (where applicable) → Customer**

Each acceptance record must include the exact release tag/SHA, environment, date/time, tested scope, exceptions and sign-off owner.

## 8. Final boundary

A successful repository certification is not production deployment evidence. Commercial go-live remains blocked until target deployment, live integrations, measured reliability/DR, deployed security testing, operational ownership and required external acceptance are evidenced.
