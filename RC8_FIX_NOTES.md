# RC8 Fix Notes — Staging Startup Blockers

## Fixes included

1. Fixed `CORS_ORIGINS` in `backend/docker-compose.yml` for `api`, `worker`, and `beat` to use valid JSON array values expected by `pydantic-settings`.
2. Fixed missing `InboxMessageCreate` import in `backend/app/api/v1/inbox.py`, which previously caused API startup to fail with `NameError`.

## Verification

- Python compile of backend application: PASS
- Compose CORS entries: 3/3 converted to JSON arrays
- `InboxMessageCreate` import: PASS

These fixes must still be validated on the user's Docker staging environment with `docker compose up -d --build` and service health checks.

## Docker LM Studio runtime configuration

The Docker Compose `api`, `worker`, and `beat` services now receive `LM_STUDIO_BASE_URL` with a Docker-safe default of `http://host.docker.internal:1234/v1`. This preserves the application default of `http://127.0.0.1:1234/v1` for non-Docker execution while allowing containers to reach LM Studio running on the Windows host.

Override with `LM_STUDIO_BASE_URL` in a project `.env` when a different endpoint is required.
