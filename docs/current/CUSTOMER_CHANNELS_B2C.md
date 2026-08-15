# B2C Customer Channels & AI Employee Conversations

## Purpose

This release adds the missing customer-facing layer between a tenant's purchased AI Employee and the tenant's own customers.

A store owner remains a **B2B tenant user** and uses the authenticated dashboard. The store's shoppers are **B2C end customers** and do not receive platform accounts.

```text
Store Owner (B2B)
  -> Employee
  -> Publish Customer Channel
  -> Website Widget / Public Chat
  -> End Customer (B2C)
  -> Conversation
  -> Run
  -> AI Gateway / RAG / Memory / Tools
```

## Implemented channels

### 1. Public Chat

Every published channel has a public key and a customer-facing URL:

`/chat/{public_key}`

This URL can be shared in social media, QR codes, SMS, email, or a product page.

### 2. Website Widget

A tenant can embed the public chat as an iframe-backed widget with:

```html
<script src="https://YOUR_PLATFORM_HOST/widget.js?channel=pk_..." async></script>
```

The script creates a fixed customer chat iframe. The customer never needs an AI Employee Platform login.

## Conversation model

The runtime hierarchy is:

```text
Tenant
  -> Employee
     -> CustomerChannel
        -> CustomerConversation
           -> CustomerMessage
              -> Run
```

`Run.conversation_id` connects the existing AI execution engine to the persistent B2C conversation. The existing RunService, AI Gateway, RAG, Memory, Tool Registry, approval boundary, billing quota, and audit path remain the execution system; B2C chat does not create a second AI runtime.

## Customer identity

The first version supports anonymous customers. A conversation receives a high-entropy customer token. Only a SHA-256 hash is stored in PostgreSQL. The browser keeps the raw token locally and sends it as `X-Customer-Token`.

Optional customer fields:

- name
- email
- phone

No customer platform account is required.

## Owner APIs

Authenticated with the existing tenant RBAC:

- `POST /api/v1/customer-channels` — publish a channel for an employee
- `GET /api/v1/customer-channels` — list channels
- `GET /api/v1/customer-channels/conversations` — list B2C conversations for the tenant

The owner dashboard can create a web channel from the Employee detail page and receives a public chat URL plus an embeddable widget snippet.

## Public APIs

No platform JWT is required:

- `GET /api/v1/public/chat/channels/{public_key}`
- `POST /api/v1/public/chat/channels/{public_key}/conversations`
- `GET /api/v1/public/chat/conversations/{conversation_id}` with `X-Customer-Token`
- `POST /api/v1/public/chat/conversations/{conversation_id}/messages` with `X-Customer-Token`

The public API never accepts a tenant ID from the browser. Tenant and employee scope are resolved from the public channel key and persisted conversation.

## Message lifecycle

1. Customer opens the public URL/widget.
2. Browser creates a conversation and receives a customer token.
3. Customer sends a message.
4. The API persists the user message.
5. The existing `RunService.create_run()` creates a tenant-scoped Run with `created_by=NULL` and links it to the conversation.
6. Celery executes the normal AI Employee runtime.
7. On successful completion, the assistant response is persisted as a `CustomerMessage` linked to the Run.
8. The browser polls the conversation and displays the response.

## Security requirements

- Public keys identify channels; they are not customer conversation credentials.
- Conversation reads/writes require the per-conversation customer token.
- Customer token hashes, not raw tokens, are stored in the database.
- Employee lookup is tenant-scoped when a channel is created.
- Public clients cannot submit `tenant_id`, `employee_id`, or `run_id` as authority fields.
- Existing RunService tool authorization and human-approval boundaries remain active.
- Production should add per-channel allowed origins and rate limits before enabling high-volume public traffic.
- Production should place the public frontend/API behind HTTPS.

## Database migration

Migration:

`fb2c3d4e5f67_customer_channels_conversations.py`

It adds:

- `customer_channels`
- `customer_conversations`
- `customer_messages`
- `runs.conversation_id`

Run:

```bash
alembic upgrade head
```

## Product flow example: shoe store

A shoe store buys the `Sales Assistant` employee.

The owner opens:

`Employees -> Sales Assistant -> Publish to your customers`

The platform creates:

`/chat/pk_...`

The owner puts the widget on the store website. A shopper opens it and asks:

> I need running shoes under €150 for a wide foot.

The Sales Assistant uses the same Employee Version, knowledge, memory, and tools configured by the store. The shopper sees only the public chat experience. The store owner can later inspect the conversation from the authenticated dashboard.

## Next channel extensions

The current abstraction intentionally separates `CustomerChannel` from `Employee`. This allows later adapters without changing the AI runtime:

- WhatsApp
- Instagram
- Telegram
- API / headless commerce

Each adapter should translate its inbound/outbound messages into the same `CustomerConversation` and `CustomerMessage` model.
