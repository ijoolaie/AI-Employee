# RC8 TestFix7 — Docker Compose Variable Interpolation

## Problem

Docker Compose emitted warnings that `HOSTNAME` and `HOST_IP` were unset. The frontend healthcheck used shell variables with single `$` signs inside the Compose file, so Compose interpolated them before the command reached the container shell.

## Fix

Escaped the shell variables in `docker-compose.yml`:

- `$$HOSTNAME`
- `$$HOST_IP`
- `$$1` in the `awk` expression

The resulting command still resolves the container IP and probes `/login` on port 3000.

## Expected result

`docker compose up -d --build` and `docker compose down` should no longer emit the `HOSTNAME` / `HOST_IP` unset warnings. The frontend healthcheck should remain healthy.

## Existing verification carried forward

- Frontend health: PASS
- Backend pytest: 150 passed
- E2E dependency check: PASS
- LM Studio smoke test: PASS
