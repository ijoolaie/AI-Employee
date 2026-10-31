# Customer handoff notification semantics

## Destination and enqueue
- Staff notification email is opt-in and tenant-scoped through `Tenant.settings.customer_handoff_notification_email`.
- The application does not invent a recipient or fall back to a global default. The notification is queued only when a tenant destination and SMTP host/from address are configured.
- The deduplicated `email.send` outbox row is created in the same database transaction as the customer handoff state transition. Its tenant-scoped dedupe key is `customer-handoff:{conversation_id}`.
- Notification content is limited to operational identifiers (tenant, conversation, channel) and avoids customer message text or unnecessary customer PII.

## What each state means
- **Pending / processing:** the outbox item is queued or claimed by the dispatcher; no delivery claim is made.
- **Dispatched:** the email worker's SMTP `send_message` call returned successfully and the resulting outbox state was committed. This means the configured SMTP server accepted the message. It does not prove inbox placement, that a human read it, or that a human responded.
- **Retry / dead:** a failure occurred before the irreversible SMTP side-effect boundary; retry/backoff or dead-letter state is persisted and observable.
- **Uncertain:** an exception occurred after the SMTP side-effect boundary. The provider may have accepted the message, so the worker does not automatically retry and risk duplicate notification.

## Assignment and acknowledgement
- A notification being dispatched does not assign a staff member and does not complete a human handoff.
- Assignment is represented by the tenant-scoped `assigned_user_id` on the conversation.
- Human acknowledgement is represented by the persisted acknowledgement actor and timestamp written by the handoff acknowledgement path.
- A conversation in human handoff does not create another AI Run until explicitly resumed.

## SLA policy
- No response-time SLA timer is currently claimed or activated.
- Before defining one, the product/operator must name the responsible owner or rotation, define the response threshold, business-hours/time-zone behavior, escalation path, and the event that starts/stops the clock.
- Until that policy is approved and measurable, the customer-facing acknowledgement must not imply that a human has been assigned or will respond within a promised time.

## Validation boundary (2026-10-31)
- PostgreSQL handoff persistence/tenant-isolation suite: 2 passed.
- Additional handoff acknowledgement/follow-up, behavior, notification outbox, dispatcher and email-worker regression group: 25 passed.
- The actual email worker delivered a synthetic handoff notification to a local Mailpit SMTP sink; Mailpit confirmed receipt and PostgreSQL confirmed the outbox row reached `dispatched`.
- This is local non-production evidence, not a real SMTP provider, inbox placement, staff response, or SLA validation.
