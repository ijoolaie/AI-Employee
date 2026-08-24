# Upgrade / Migration Runbook

## Before upgrade

1. Record current release version, commit SHA and Alembic head.
2. Confirm a fresh backup exists and restore verification is known.
3. Review the target release manifest and compatibility matrix.
4. Confirm rollback artifact is available.
5. Put customer-facing maintenance/upgrade notice in place when required.

## Upgrade

```bash
docker compose --env-file .env -f docker-compose.production.yml pull
docker compose --env-file .env -f docker-compose.production.yml up -d --build
```

Run the repository-approved Alembic migration command for the target release. Do not skip migrations or manually alter migration history.

## Verify

```bash
docker compose --env-file .env -f docker-compose.production.yml ps
docker compose --env-file .env -f docker-compose.production.yml logs --tail=100 api worker
```

Verify API dependency health, frontend login, background worker health, scheduled beat, and critical customer workflows.

## Failure

Stop rollout if health checks, migrations, or acceptance checks fail. Preserve logs and deployment metadata. Do not attempt ad-hoc schema changes.

## Completion record

Record target version, source commit, migration head before/after, start/end time, operator, backup reference, acceptance result and any exception.
