# Execution Runbook — Windows Development

## Terminal layout

Use these terminals:

**T1 — infrastructure**
```powershell
cd <project>ackend
docker compose up -d postgres redis
```

**T2 — API**
```powershell
cd <project>ackend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**T3 — worker**
```powershell
cd <project>ackend
.\.venv\Scripts\Activate.ps1
python -m celery -A app.workers.celery_app worker -l info --pool=solo
```

**T4 — frontend**
```powershell
cd <project>rontend
npm run dev
```

**Optional T5 — beat**
```powershell
cd <project>ackend
.\.venv\Scripts\Activate.ps1
python -m celery -A app.workers.celery_app beat -l info
```

## Health checks

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/dependencies
```

Expected: HTTP 200. The dependency endpoint should report PostgreSQL/Redis as reachable.

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
