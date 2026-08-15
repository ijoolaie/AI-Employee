# Phase 1 — DLQ, Replay & Observability — v0.2.37

## Implemented
- Outbox dead-letter state after configurable maximum attempts.
- Dead-letter timestamps and replay timestamps.
- Tenant-scoped dead-letter inspection and replay API.
- Operational metrics snapshot API.
- Prometheus `/metrics` endpoint.
- Optional OpenTelemetry SDK initialization with configurable OTLP endpoint.
- New migration `f7c8d9e0a123`.

## Verification status
- Static Python compilation: to be run in release build.
- PostgreSQL migration execution: NOT VERIFIED in the current environment.
- Redis/Celery E2E: NOT VERIFIED unless Docker/Redis/PostgreSQL services are available.
- Prometheus endpoint is code-level implemented; runtime scrape verification requires the stack.
