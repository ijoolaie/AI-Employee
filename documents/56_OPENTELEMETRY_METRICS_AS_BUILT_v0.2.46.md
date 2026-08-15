# Phase 1 — OpenTelemetry + Metrics As-Built v0.2.46

## Scope

This release completes the Phase 1 observability instrumentation layer on top of the durable Trace/Cost/Replay surfaces already present in v0.2.45.

## OpenTelemetry

- Centralized bootstrap in `backend/app/core/telemetry.py`.
- Configurable OTLP HTTP exporter via `OTEL_EXPORTER_ENDPOINT` / application settings.
- Resource attributes include service name, service version and deployment environment.
- FastAPI automatic instrumentation.
- SQLAlchemy automatic instrumentation.
- Manual spans for AI Gateway calls, Employee Run execution, Workflow execution, parallel branches, Outbox dispatch and generic Celery tasks.
- Request ID is attached to the active HTTP span.
- Telemetry is fail-open: an unavailable exporter cannot prevent application startup or request execution.

## Prometheus Metrics

Metrics are exposed at `GET /metrics`.

Coverage includes:

- HTTP request count and latency.
- Workflow execution outcomes and latency.
- Workflow step starts/retry starts.
- AI provider calls, latency, tokens and cost.
- Transactional Outbox dispatch, retry and DLQ counters.
- Durable Outbox queue gauges.
- Workflow run/step row gauges.
- Redis broker queue depth gauge.
- PostgreSQL/Redis dependency health gauges.
- Celery task count and latency.

Metric labels intentionally avoid tenant/user IDs to prevent unbounded Prometheus cardinality. Tenant-scoped detail remains available through the authenticated operations metrics endpoint and durable Trace/Usage APIs.

## Verification Contract

Static source compilation and targeted observability contract tests are required for this release. Full PostgreSQL/Redis/Celery/LM Studio E2E remains environment-dependent and must not be reported as PASS unless those services are actually running.
