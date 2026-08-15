# Workflow Event Triggers & Webhooks — As-Built v0.2.30

## Delivered
- Tenant-scoped workflow event triggers.
- Public webhook ingestion endpoint with UUID trigger routing.
- Event type validation.
- HMAC-SHA256 webhook signature validation.
- Durable event delivery records.
- Idempotency by `(trigger_id, event_id)` unique constraint.
- Event dispatch through Celery after the delivery transaction commits.
- Event payload is injected into workflow input under `event`, with `event_id` and `event_type`.
- Event trigger RBAC: `workflow.event.read`, `workflow.event.write`, `workflow.event.ingest`.
- Audit coverage for trigger creation and event dispatch.

## Security note
The current implementation stores the webhook secret in the database so HMAC verification is possible. Production hardening should replace this with an application-level encrypted secret store before external internet exposure.

## Boundary
This release does not claim a full external integration catalog, signed outbound webhooks, replay UI, rate limiting, or WAF-level protection.
