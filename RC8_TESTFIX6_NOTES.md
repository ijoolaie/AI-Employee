# RC8 TESTFIX6 — Dedicated Frontend Build/Certification

## Finding

The backend image is a Python runtime and correctly has no `npm`. Attempting `npm run build` through `docker compose exec api` is therefore not a valid frontend certification procedure.

## Changes

- Added `frontend/Dockerfile` using Node 22 multi-stage build.
- Frontend image runs `npm run test` and `npm run build` during image build.
- Enabled Next.js `output: "standalone"` for a minimal production runtime.
- Added a dedicated `frontend` Compose service on port 3000.
- Added frontend healthcheck against `/login`.
- Kept frontend out of the Python image's runtime responsibility.
- Added frontend certification runbook.

## Certification rule

Backend `pytest` and E2E dependency checks remain independently certified. Frontend certification requires the dedicated frontend image to build successfully, its contract tests to pass, and the runtime healthcheck to become healthy.
