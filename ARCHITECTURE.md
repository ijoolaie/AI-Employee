# RC8 Repository Architecture

This repository is intentionally split by deployable responsibility:

- `backend/` — FastAPI application, Celery workers/beat, migrations, scripts, tests.
- `frontend/` — Next.js application and frontend tests.
- `docker-compose.yml` — single orchestration entry point at repository root.
- `docs/` — current architecture, release, runbook and product documentation.
- `ops/` — operational/load-test assets.
- `.github/` — CI/CD workflows.

Run Compose commands from the repository root, not from `backend/`:

```powershell
docker compose config --services
docker compose up -d --build api worker beat frontend
```

The backend image uses the repository root as its build context and `backend/Dockerfile`.
The frontend image uses the repository root as its build context and `frontend/Dockerfile`.
## Docker build boundary

The repository root is the Docker Compose context. `backend/Dockerfile` builds only the Python backend and does not copy `docker-compose.yml` or the frontend. `frontend/Dockerfile` independently builds the Next.js application. This keeps service boundaries clean and prevents backend builds from depending on frontend files.
