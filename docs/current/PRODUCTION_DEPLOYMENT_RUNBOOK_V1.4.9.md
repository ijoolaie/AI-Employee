# v1.4.9 Production Deployment Runbook

**Status:** READY FOR EXTERNAL EXECUTION  
**Release:** v1.4.9  
**Certified SHA:** f1ce20c010779f5273eb5d0051da24cdd57b33f6  
**Production Certification:** run 35575615877 / job 106256713583 — PASS  
**Evidence artifact SHA256:** 32962353a3511d7d5ae951eb6d0a44620a10211493730544342afe55f980a896

> This runbook is an execution guide. It does not claim that production has been deployed. The external production gate remains open until target-specific evidence is captured.

## 1. Target baseline

Recommended initial target:

- Ubuntu 24.04 LTS
- 8 vCPU
- 16 GB RAM
- 150–200 GB NVMe/SSD
- fixed public IP
- Docker Engine + Compose v2
- TLS reverse proxy/ingress
- encrypted off-host backups
- centralized monitoring/logging
- no GPU required when inference is remote

Keep PostgreSQL, Redis and application storage private to the Docker network unless a specific managed-service design requires otherwise.

## 2. Services

The production Compose topology contains:

- PostgreSQL 16
- Redis 7
- storage-init
- API
- Celery worker
- Celery Beat
- Next.js frontend

The repository production Compose file currently has no TLS/reverse-proxy service. TLS termination, DNS, firewall and public ingress therefore belong to the external target layer.

## 3. Required external inputs

Provide through the approved secret/configuration system:

### Required application configuration

- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB
- DATABASE_URL
- DATABASE_URL_SYNC
- REDIS_PASSWORD
- REDIS_URL
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND
- SECRET_KEY
- CORS_ORIGINS
- FRONTEND_BASE_URL
- FRONTEND_APP_URL
- NEXT_PUBLIC_API_URL

### Required infrastructure configuration

- production hostname/domain
- TLS certificate/private-key lifecycle
- firewall policy
- SSH/deployment identity
- persistent backup destination
- monitoring and alert destination
- deployment operator and rollback owner

### Optional providers

Only enable providers required by the launch scope:

- Stripe
- Shopify
- SMTP
- configured AI provider
- object storage

Provider credentials must be supplied externally and validated with production-safe test inputs.

## 4. Pre-deployment admission

Before touching the live target:

1. Confirm release identity is exactly `v1.4.9` / `f1ce20c010779f5273eb5d0051da24cdd57b33f6`.
2. Verify the release assets/checksums from the GitHub release.
3. Confirm the target currently runs a supported version.
4. Record current application commit and Alembic head.
5. Confirm the previous known-good application release and rollback artifact.
6. Create and independently verify a fresh PostgreSQL backup.
7. Confirm backup storage is outside the primary failure domain.
8. Confirm DNS/TLS/firewall/SSH access.
9. Confirm secrets exist without printing their values.
10. Confirm monitoring and alert delivery are reachable.

**Hard stop:** do not migrate if the fresh backup or rollback target is unavailable.

## 5. Recommended deployment sequence

On the production host:

```bash
git clone --depth 1 --branch v1.4.9 https://github.com/ijoolaie/AI-Employee.git ~/ai-employee-releases/v1.4.9
cd ~/ai-employee-releases/v1.4.9

docker compose --env-file /path/to/.env -f docker-compose.production.yml config --quiet

docker compose --env-file /path/to/.env -f docker-compose.production.yml build api worker beat frontend

ENV_FILE=/path/to/.env \
COMPOSE_FILE=docker-compose.production.yml \
bash scripts/production_migrate.sh

docker compose --env-file /path/to/.env -f docker-compose.production.yml up -d api worker beat frontend
```

The migration gate must complete before application services are started. Verify that the database reaches the single Alembic head and that `alembic check` passes.

## 6. Immediate health verification

Run:

```bash
docker compose --env-file /path/to/.env -f docker-compose.production.yml ps

docker compose --env-file /path/to/.env -f docker-compose.production.yml logs --tail=100 api worker beat frontend
```

Required:

- postgres healthy
- redis healthy
- API healthy
- frontend healthy
- worker running
- beat running
- migration head equals the release head
- no startup secret/configuration errors

Then verify externally:

- HTTPS certificate validation
- frontend login
- API authenticated request
- one controlled background job
- one enabled provider smoke test
- audit event generation
- tenant/RBAC negative path

## 7. Reverse proxy / TLS

Because the repository Compose file does not terminate public TLS, deploy a hardened external ingress.

Minimum rules:

- only 80/443 public as required; redirect HTTP to HTTPS
- SSH restricted to approved administration sources
- PostgreSQL/Redis never publicly exposed
- valid certificate and automatic renewal
- HSTS after confirming HTTPS correctness
- upstream only to frontend/API as designed
- request-size and timeout limits appropriate to file upload/API workloads
- access logs without secrets or authorization headers
- trusted-host/origin configuration matches the public hostname

Record certificate issuer, expiry, renewal mechanism and ingress configuration version.

## 8. Backup and restore

Backup:

```bash
DATABASE_URL_SYNC='REDACTED-VIA-SECRET-MANAGER' \
BACKUP_DIR='/secure/backup/path' \
./scripts/backup_postgres.sh
```

Verify the generated checksum and archive table of contents.

Restore only into an isolated recovery database:

```bash
TARGET_DATABASE_URL='REDACTED-VIA-SECRET-MANAGER' \
./scripts/restore_postgres.sh /secure/backup/path/postgres-backup-<timestamp>.dump
```

Do not restore directly over the serving database during validation.

Record:

- backup timestamp
- backup size
- checksum
- restore start/end
- restored migration head
- representative data-integrity checks
- observed RPO
- observed RTO

Engineering targets are RPO <= 15 minutes and RTO <= 60 minutes; these are not production claims until measured on the target.

## 9. Rollback

Application rollback is the default first response.

1. Stop new rollout.
2. Preserve logs and deployment metadata.
3. Identify the last known-good application release.
4. Verify its artifact/checksum.
5. Redeploy the known-good application revision.
6. Do not casually downgrade database migrations.
7. If schema/data recovery is required, use the verified backup and controlled recovery procedure.
8. Re-run health, authorization, worker and critical-workflow checks.
9. Record the final decision and recovery duration.

Database downgrade is not the normal rollback path.

## 10. Production evidence pack

Capture, without secrets or customer PII:

- release tag and exact deployed SHA
- artifact checksums
- deployment timestamp UTC
- target hostname/service identifier
- operator
- image/build identity
- migration head before/after
- health/readiness results
- TLS/network evidence
- backup/checksum/restore evidence
- observed RPO/RTO
- SLO/SLI measurements
- provider smoke/failure/retry evidence
- Vendor → Reseller → Client actor matrix
- DAST result and remediation status
- independent security review result
- HA/failure-recovery result
- incident/on-call drill result
- vendor/reseller/customer acceptance

## 11. Launch blockers still external

The repository is release-certified, but the following remain target-specific gates:

- real production deployment
- live providers
- durable backup/restore and measured RPO/RTO
- production SLO/SLI and alerts
- TLS/network perimeter
- external secret-manager lifecycle
- deployed authenticated DAST
- independent security review
- HA/failure recovery
- incident response/on-call
- Vendor/Reseller/Customer acceptance

Do not mark these complete from CI or local Docker evidence.

## 12. Deployment automation audit

The repository contains a `production-live-deploy.yml` workflow that can deploy a release over SSH when the GitHub production environment is configured. Before using it for v1.4.9, verify its external secrets and environment configuration.

Current automation observations:

- it validates the release ref format;
- it uses strict SSH host-key verification;
- it writes the environment file with mode 600;
- it checks Compose configuration and service health;
- it records deployed ref/SHA/timestamp;
- it runs the repository migration gate before application startup.

Important operational gaps to close or consciously accept:

1. The workflow default release ref is stale and must not be used as a production selection.
2. The workflow builds images on the target host rather than deploying independently signed/pinned image digests.
3. The workflow does not itself create the required pre-migration backup.
4. TLS/reverse-proxy configuration is outside the Compose stack and must be verified separately.
5. The workflow does not itself prove backup durability, RPO/RTO, SLO/SLI, DAST, pentest, HA or customer acceptance.

For the first real deployment, the operator must execute the pre-deployment admission checks in this runbook even if the GitHub deployment workflow is used.

## 13. Evidence status

Current repository evidence:

- v1.4.9 exact-SHA Production Certification: PASS
- release publication: PASS
- production deployment: NOT VERIFIED
- customer acceptance: NOT VERIFIED

The correct boundary remains:

`Engineering Ready ≠ Release Certified ≠ Production Deployed ≠ Commercially Accepted`
