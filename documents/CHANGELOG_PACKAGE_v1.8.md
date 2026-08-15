# Package Changelog v1.8

## v0.2.30 — Workflow Event Triggers & Webhooks

- Reconciled the empty v0.2.29 archive by using the latest non-empty executable baseline v0.2.28.
- Re-applied the planned v0.2.29 condition-step and scheduling capabilities.
- Added tenant-scoped event triggers and durable webhook deliveries.
- Added HMAC-SHA256 webhook validation and event idempotency by trigger/event ID.
- Added Celery dispatch for event-driven Workflow Runs.
- Added schedule tick support and condition routing.
- Added event-specific RBAC permissions and audit events.
- Added focused source-level tests and documented the real pytest dependency limitation.

## v0.2.31
- Workflow Human Approval + Wait/Resume
