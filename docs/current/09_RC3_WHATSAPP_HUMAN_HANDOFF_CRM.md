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

The endpoint maps the phone number to a persistent customer and conversation, creates a Run through the existing Run Service, and queues the AI Employee worker. Meta-specific verification and inbound parsing are implemented at `/api/v1/webhooks/channels/whatsapp/meta/{channel_id}`; the provider-neutral endpoint remains available for integrations that already verify their own requests.

Outbound Meta Cloud API delivery is implemented by `WhatsAppCloudAdapter`, which resolves an opaque Credential Vault reference and returns the provider message ID when present. Outbound calls must enter through the governed `whatsapp.send_text` Tool Registry and approval-bound outbox worker. Direct calls to the lower-level delivery adapter do not themselves enforce human approval.

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

RC3 remains a foundation release, not WhatsApp production certification. The Meta Cloud API adapter and approval-gated outbound path exist, but production readiness still requires:

1. Configure and verify a real Meta Business/WhatsApp Cloud API account, phone-number ID, and tenant-scoped opaque Credential Vault reference.
2. Validate the webhook verification token and app-secret configuration through the actual Meta console and a publicly reachable HTTPS endpoint.
3. Add a provider-sandbox or explicitly authorized test-number acceptance run covering approved outbound send, provider message ID persistence, and provider status callbacks. Do not use a live customer recipient for acceptance.
4. Persist and expose provider delivery/read/failure status callbacks; current outbound success records the provider's immediate acceptance, not final delivery.
5. Define manual reconciliation for outbox rows marked `uncertain`; do not automatically retry after the provider request boundary because duplicate delivery is possible.
6. Add agent assignment/presence and SLA controls.
7. Add CRM profile detail, conversation timeline, notes and tags editing.
8. Add E2E tests for customer → AI → human → customer.

Contract tests for the Cloud API adapter mock the HTTP client and Credential Vault resolution. They validate request construction, credential isolation, response handling, and fail-closed behavior; they do not prove external connectivity or real Meta delivery.

## Release acceptance

A feature is not considered complete until its API, data model, frontend route/navigation, onboarding visibility, and relevant dashboard surface are updated together.
