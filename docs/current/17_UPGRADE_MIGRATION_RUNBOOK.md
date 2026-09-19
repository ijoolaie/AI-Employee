# Upgrade / Migration Runbook

## Before upgrade

1. Record current release version, commit SHA and Alembic head.
2. Confirm a fresh backup exists and restore verification is known.
3. Review the target release manifest and compatibility matrix.
4. Confirm rollback artifact is available.
5. Put customer-facing maintenance/upgrade notice in place when required.

## Upgrade

Build the target application images without starting application services:

```bash
docker compose --env-file .env -f docker-compose.production.yml pull
docker compose --env-file .env -f docker-compose.production.yml build api worker beat frontend
```

Run the repository-approved migration gate **before** starting API, worker, beat, or frontend:

```bash
ENV_FILE=.env COMPOSE_FILE=docker-compose.production.yml bash scripts/production_migrate.sh
```

Do not skip migrations or manually alter migration history. The migration runner fails if the database does not reach the single Alembic head or if `alembic check` reports schema drift.

Only after the migration gate succeeds:

```bash
docker compose --env-file .env -f docker-compose.production.yml up -d api worker beat frontend
```

## Verify

```bash
docker compose --env-file .env -f docker-compose.production.yml ps
docker compose --env-file .env -f docker-compose.production.yml logs --tail=100 api worker
```

Verify API dependency health, frontend login, background worker health, scheduled beat, and critical customer workflows.

## Failure

Stop rollout if health checks, migrations, or acceptance checks fail. Preserve logs and deployment metadata. Do not attempt ad-hoc schema changes. If the migration gate fails, application services must remain stopped until the database compatibility issue is resolved.

## Completion record

Record target version, source commit, migration head before/after, start/end time, operator, backup reference, acceptance result and any exception.
