# Execution Runbook — Windows Development

## Terminal layout

Use these terminals:

**T1 — infrastructure**
```powershell
cd <project>\backend
docker compose up -d postgres redis
```

**T2 — API**
```powershell
cd <project>\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**T3 — worker**
```powershell
cd <project>\backend
.\.venv\Scripts\Activate.ps1
python -m celery -A app.workers.celery_app worker -l info --pool=solo
```

**T4 — frontend**
```powershell
cd <project>\frontend
npm run dev
```

**Optional T5 — beat**
```powershell
cd <project>\backend
.\.venv\Scripts\Activate.ps1
python -m celery -A app.workers.celery_app beat -l info
```

## Health checks

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/dependencies
```

Expected: HTTP 200. The dependency endpoint should report PostgreSQL/Redis as reachable.

## Local production-like validation stack

The repository's `docker-compose.local-production.yml` is intended for a production-like validation stack that can run beside the normal development stack on Windows. It deliberately binds alternate host ports to avoid collisions with the default local compose services:

| Service | Host port | Container port |
|---|---:|---:|
| PostgreSQL | `15432` | `5432` |
| Redis | `16379` | `6379` |
| API | `18000` | `8000` |
| Frontend | `13000` | `3000` |

The validation environment keeps these bindings local-only (`127.0.0.1`). The application still uses the internal Compose service names (`postgres`, `redis`) for container-to-container connectivity.

Example Windows validation commands:

```powershell
docker compose --env-file .env.production -f docker-compose.production.yml -f docker-compose.local-production.yml -p ai-employee-production up -d
Invoke-RestMethod http://127.0.0.1:18000/health
Invoke-RestMethod http://127.0.0.1:18000/health/dependencies
Invoke-WebRequest http://127.0.0.1:13000/login -UseBasicParsing
```

The local production environment file is intentionally operator-managed and ignored by Git. Do not commit production secrets.

## Stop

```powershell
docker compose stop
```

Do not use `docker compose down -v` unless you intentionally want to delete the local database volume.

## Reset local database

Only for disposable development data:

```powershell
docker compose down -v
docker compose up -d postgres redis
alembic upgrade head
```

## Troubleshooting order

1. Is Docker running?
2. Is PostgreSQL healthy?
3. Is Redis healthy?
4. Is `.env` present?
5. Does `alembic current` show the expected head?
6. Does `/health/dependencies` pass?
7. Is Celery worker connected to Redis?
8. Is LM Studio running and serving the configured model?
9. Is frontend CORS/API URL correct?
10. Only then inspect application-level errors.

## Common Windows issue

Celery's prefork pool can be problematic on Windows development. Use:

```powershell
--pool=solo
```

Production Linux workers should use an appropriate production pool/configuration.


## 11. Celery on Windows — observed behavior in this release

A real local worker test on 2026-08-11 initially used Celery 5.6.3 with the default `prefork` pool and concurrency 16. Several `SpawnPoolWorker` processes terminated with:

```text
PermissionError: [WinError 5] Access is denied
```

This is a known Windows multiprocessing/billiard class of issue and should not be used as the production deployment model.

After restarting the worker, the worker reached:

```text
celery@... ready.
```

and the real `run.execute` path completed successfully, including SQLAlchemy authorization queries and final `COMMIT`.

For Windows development, the supported runbook remains:

```powershell
python -m celery -A app.workers.celery_app worker -l info --pool=solo
```

For the client's production server, prefer Linux and a normal production Celery process configuration rather than relying on Windows `prefork`.
