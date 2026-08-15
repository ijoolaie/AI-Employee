# Staging Bootstrap

Provision PostgreSQL, Redis, Backend API, Celery worker, Celery beat/scheduler, Frontend, TLS/reverse proxy and monitoring.

Populate `STAGING_ENV.template` through the CI/CD secret manager. Do not commit real secrets.

Apply the project's normal database migrations against the staging database. Do not reset a shared staging database during certification.

Start API, workers, scheduler and frontend with the project's supported deployment manifests. Verify API readiness, frontend load, DB/Redis connectivity, worker heartbeat, scheduler heartbeat, logs and metrics before entering Phase 7.
