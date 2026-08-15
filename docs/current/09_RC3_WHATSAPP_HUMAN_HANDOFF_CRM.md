# RC3 — WhatsApp, Human Handoff, Unified Inbox & Customer CRM

## Purpose

RC3 closes the customer-service loop around the existing AI Employee platform. A tenant can now expose an Employee through a WhatsApp channel foundation, manage AI-to-human handoff in a shared inbox, and maintain persistent customer profiles.

## Product rule: every backend option updates the UI

Any new channel, capability, permission, tool, or customer workflow must be represented in all relevant surfaces:

- Business Dashboard
- AI Workspace
- Customer Channels
- Unified Inbox
- Customers / CRM
- Admin / platform operations where applicable
- Onboarding and launch checklist
- API/developer documentation

This is now a release acceptance criterion.

## WhatsApp channel

`customer_channels.channel_type` supports `whatsapp` in addition to `web_widget` and `public_chat`.

The tenant UI can create a WhatsApp channel and exposes a provider-neutral inbound webhook:

`POST /api/v1/webhooks/channels/whatsapp/{channel_id}`

Payload:

```json
{
  "from_phone": "+31612345678",
  "text": "Do you have size 42?",
  "name": "Ali",
  "message_id": "provider-message-id"
}
```

Optional `config.webhook_secret` enables HMAC-SHA256 verification through `X-Channel-Signature`.

The endpoint maps the phone number to a persistent customer and conversation, creates a Run through the existing Run Service, and queues the AI Employee worker. The endpoint intentionally remains provider-neutral; a Meta/Twilio/360dialog adapter is still required for production outbound delivery and provider-specific verification.

## Customer CRM

New `customers` table is tenant-scoped and linked to `customer_conversations.customer_id`.

Available operations:

- `GET /customers`
- `GET /customers/{id}`
- `PATCH /customers/{id}`

Customer fields include:

- name
- email
- phone
- tags
- notes
- last channel
- external key

The frontend adds a **Customers (CRM)** workspace entry and a searchable customer directory.

## Human handoff

Unified Inbox now supports:

- AI handling state
- human takeover
- return to AI
- human reply
- persistent message history
- customer/channel context

Endpoints:

- `GET /inbox/conversations`
- `GET /inbox/conversations/{id}/messages`
- `POST /inbox/conversations/{id}/messages`
- `POST /inbox/conversations/{id}/handoff`

Human replies are stored as `role=human`. Public web chat reads the same conversation, so the customer can receive a human response without entering the SaaS dashboard.

## Frontend surfaces updated

- Customer Channels: WhatsApp option and webhook configuration surface
- Unified Inbox: conversation list + transcript + takeover + human reply
- Customers: searchable CRM directory
- Sidebar: Customers (CRM)
- Customer Conversations remains available as a reporting/list view

## Production gaps

RC3 is a foundation release, not WhatsApp production certification. Before launch:

1. Add and verify a Meta WhatsApp Cloud API or approved BSP adapter.
2. Implement provider verification handshake and signed webhook verification according to the selected provider.
3. Implement outbound message delivery and retry/idempotency.
4. Add provider message IDs and delivery/read states.
5. Add agent assignment/presence and SLA controls.
6. Add CRM profile detail, conversation timeline, notes and tags editing.
7. Add E2E tests for customer → AI → human → customer.

## Release acceptance

A feature is not considered complete until its API, data model, frontend route/navigation, onboarding visibility, and relevant dashboard surface are updated together.
