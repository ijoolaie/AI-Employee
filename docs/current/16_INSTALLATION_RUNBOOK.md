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

## 4. Start

```bash
docker compose --env-file .env -f docker-compose.production.yml up -d --build
```

## 5. Verify health

```bash
docker compose --env-file .env -f docker-compose.production.yml ps
docker compose --env-file .env -f docker-compose.production.yml logs --tail=100 api
```

Confirm API, worker, beat, frontend, Postgres and Redis are healthy before acceptance.

## 6. Database migration

Run the repository-approved Alembic migration procedure before opening customer traffic. Record the resulting migration head in the deployment record.

## 7. Acceptance

Complete the Customer Acceptance Checklist and record release version, commit SHA, migration head, operator, date and exceptions.
