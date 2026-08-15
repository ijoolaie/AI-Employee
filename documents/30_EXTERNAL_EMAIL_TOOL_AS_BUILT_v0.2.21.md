# External Email Tool — As-Built v0.2.21

## Purpose

This release crosses the first external side-effect boundary: an AI Employee may request an email send, but the action is not executed merely because the model requested it. The request must pass every existing security boundary and an explicit human approval.

## Execution boundary

`EmployeeVersion.allowed_tools` → Tool Registry registration → JSON Schema validation → worker-side `run.execute` permission check → `requires_approval=True` → durable approval request → explicit `approval.decide` → Celery resume → SMTP send → `tool.call` Audit Log.

## Tool

`send_email` accepts:

- `to`: 1–10 unique email addresses
- `subject`: 1–200 characters
- `body`: 1–10,000 characters

The Tool does not support attachments, arbitrary headers, CC/BCC, HTML, or arbitrary SMTP hosts. This intentionally keeps the first external side-effect narrow and auditable.

## SMTP configuration

Real credentials are supplied only through `.env` / deployment secrets:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_USE_STARTTLS`
- `SMTP_ALLOWED_RECIPIENT_DOMAINS`

The recipient-domain allowlist is fail-closed: when it is empty, the Tool refuses execution even after human approval.

## Security

- No direct API endpoint executes the Tool.
- Model ToolCall alone cannot authorize the action.
- Approval is durable and tenant-scoped.
- SMTP credentials never enter the model prompt, Tool arguments, Audit metadata, or release ZIP.
- The handler uses the configured SMTP server only; it does not accept a model-controlled host.

## Testing

The SMTP integration is tested with a mocked SMTP transport. No live email is sent by automated tests.

## Deferred

- HTML email / templates
- Attachments
- Provider-specific transactional email APIs
- Delivery status/webhooks
- Per-tenant sender policies
- Quotas and billing for external actions
