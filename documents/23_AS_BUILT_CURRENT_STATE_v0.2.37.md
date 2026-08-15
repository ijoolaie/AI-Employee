# AS-BUILT CURRENT STATE — v0.2.37

## Phase 1 additions
- Transactional outbox messages now transition to `dead` after `outbox_max_attempts`.
- Dead-letter messages retain error/attempt/dead/replay metadata.
- Tenant-scoped DLQ listing and replay APIs are available under `/api/v1/operations`.
- `/metrics` exposes Prometheus process metrics; HTTP request count/latency are recorded.
- OpenTelemetry request spans are initialized when enabled; OTLP export is optional via `OTEL_EXPORTER_ENDPOINT`.

## Verification
- Targeted v0.2.37 contract tests: PASS.
- Python compilation: PASS.
- Migration graph static check: PASS; current head is `f7c8d9e0a123`.
- Real PostgreSQL/Redis/Celery E2E: NOT VERIFIED in this environment.
