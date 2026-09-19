# Installation Runbook

## Preconditions

- Supported Docker Engine/Compose environment.
- Release archive and `SHA256SUMS` received from the vendor.
- Customer DNS/TLS endpoint prepared.
- Secret-management method selected.
- Backup destination selected.

## 1. Verify release

```bash
sha256sum -c SHA256SUMS
```

Confirm the archive version and `source_commit_sha` in `RELEASE-MANIFEST.json`.

## 2. Prepare configuration

```bash
python scripts/generate_customer_config.py --domain customer.example.com
```

Copy the generated template to the deployment host as `.env`, replace every required placeholder, and keep it outside source control.

## 3. Validate Compose

```bash
docker compose --env-file .env -f docker-compose.production.yml config
```

Do not continue if interpolation errors or missing required variables are reported.

## 4. Build application images

```bash
docker compose --env-file .env -f docker-compose.production.yml build api worker beat frontend
```

## 5. Bootstrap infrastructure and migrate

Do **not** start API, worker, beat, or frontend before the database migration gate succeeds. Use the repository migration runner:

```bash
ENV_FILE=.env COMPOSE_FILE=docker-compose.production.yml bash scripts/production_migrate.sh
```

The runner starts only PostgreSQL, Redis, and storage initialization, waits for PostgreSQL, runs `alembic upgrade head`, verifies the current revision matches the single Alembic head, and runs `alembic check`.

Record the reported migration head in the deployment record.

## 6. Start application services

```bash
docker compose --env-file .env -f docker-compose.production.yml up -d api worker beat frontend
```

## 7. Verify health

```bash
docker compose --env-file .env -f docker-compose.production.yml ps
docker compose --env-file .env -f docker-compose.production.yml logs --tail=100 api worker beat
```

Confirm API, worker, beat, frontend, Postgres and Redis are healthy before acceptance. The migration gate must already have passed before background workers are allowed to start.

## 8. Acceptance

Complete the Customer Acceptance Checklist and record release version, commit SHA, migration head, operator, date and exceptions.
