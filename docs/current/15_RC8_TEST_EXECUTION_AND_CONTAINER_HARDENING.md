# RC8 — Test Execution & Container Hardening

## Finding
The backend image previously did not copy the `tests/` directory into `/app`, so running `pytest -q` inside the API container produced `No files were found in testpaths` and could not constitute a valid test result.

## Fix
- Docker image now copies `tests/` into `/app/tests`.
- Backend container runs as non-root `appuser` (UID 10001).
- `/app` is owned by `appuser`, allowing Celery Beat's persistent schedule file to remain writable.

## Certification rule
An empty/no-test pytest run is **not** a PASS. RC8 remains BLOCKED until the real backend test suite executes and reports its result.

## Next staging commands
```powershell
docker compose up -d --build api worker beat
docker compose ps
docker compose exec api pytest -q
```

Then run the real-stack dependency gate:
```powershell
docker compose exec api python scripts/e2e_stack_verify.py
```
