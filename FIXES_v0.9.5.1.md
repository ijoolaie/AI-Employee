# Fixes in v0.9.5.1 (enterprise UI package)

## 1. customer_dashboard_service.py — 500 on /api/v1/customer-dashboard
**Bug:** `await db.execute(select(...))` result was unpacked directly as two values.
In SQLAlchemy 2.0 this returns a `Result`; you must call `.one()`.

**Fix:** All multi-column aggregate queries now use `result = await db.execute(...); a, b = result.one()`.

## 2. CORS defaults for local / Docker Desktop development
**Problem:** Frontend served from `http://172.18.0.1:3000` (Docker bridge) was blocked.

**Fix:**
- Default `cors_origins` in `app/core/config.py` now includes:
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
  - `http://172.18.0.1:3000`
  - `http://host.docker.internal:3000`
- `docker-compose.yml` `CORS_ORIGINS` updated to the same list.

### Recommended `.env` line (if you override)
```env
CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000","http://172.18.0.1:3000","http://host.docker.internal:3000"]
```

After replacing files, restart uvicorn (and worker if running).
