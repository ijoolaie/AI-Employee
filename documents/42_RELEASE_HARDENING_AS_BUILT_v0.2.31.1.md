# Release Hardening — As Built v0.2.31.1

Baseline: `v0.2.31`. This is a reconciliation/maintenance release, not a feature release.

## Implemented

- Transactional outbox for workflow execution, event dispatch, approval resume, and SMTP email delivery.
- Celery Beat dispatcher polls the outbox after database commit.
- Workflow manual runs, schedules, event deliveries and approval decisions write their dispatch intent in the same DB transaction as business state.
- Event webhook ingestion no longer publishes to Celery before the request transaction commits.
- Event delivery uniqueness remains DB-enforced and duplicate webhook requests are idempotent at the delivery layer.
- SMTP `send_email` no longer sends directly from the Run transaction; it creates an `email.send` outbox message. SMTP execution happens in a worker.
- Webhook secrets created after this release are encrypted at rest using a key derived from the application `SECRET_KEY`. Existing legacy plaintext secrets remain backward-compatible and must be rotated.
- Tenant Admin defaults now include event and memory permissions in addition to workflow approval permissions.
- Application/package version is `0.2.31.1`.

## Verification policy

Claims are limited to checks executable in the build environment. Full pytest/database integration is not marked PASS when required runtime dependencies or PostgreSQL are unavailable.
