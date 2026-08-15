# SaaS Sales Readiness — v1.0.0-rc.2 foundation

## Purpose

This release adds the minimum product layer needed to turn the AI Employee platform into a sellable B2B SaaS for businesses such as shoe stores, ecommerce shops, and service businesses.

## Implemented foundations

### 1. Onboarding
`/onboarding` provides a six-step launch checklist:

1. Business type
2. Brand/setup
3. Product catalog
4. AI Employee
5. Customer channel
6. Launch verification

Progress is persisted per tenant in `onboarding_progress`.

### 2. Product Catalog
`/products` and `/api/v1/products` provide a tenant-scoped catalog with:

- SKU
- name/description
- category
- price/currency
- inventory
- attributes
- images
- source

The AI Tool Registry now exposes safe read-only tools:

- `search_products`
- `get_product`
- `check_inventory`

These tools are tenant-scoped and execute through the existing Run/Tool Registry security boundary.

### 3. Commerce Integrations foundation
`/integrations` and `/api/v1/commerce-integrations` create tenant-scoped connector records for:

- Shopify
- WooCommerce
- Magento
- Custom API
- CSV

Provider-specific OAuth/API credential flows are intentionally not faked. The connector record is the contract point for production adapters.

### 4. Unified Inbox + Human Handoff
`/inbox` provides a single tenant-scoped conversation list. Existing customer conversations now support:

- `handoff_requested`
- `assigned_user_id`
- `human` conversation status
- AI return / human takeover

The inbox reuses the existing Conversation, Message, Run, AI Gateway, RAG, Memory and Tool Registry layers.

## Production-critical next connectors

The following are still required before marketing these as production integrations:

- Shopify OAuth + product/inventory/order webhooks
- WooCommerce REST authentication + webhooks
- Magento connector
- WhatsApp Business Cloud integration
- Instagram messaging integration
- durable agent/user assignment and real-time inbox updates (WebSocket/SSE)
- customer profile/CRM table beyond conversation-level identity
- checkout/order placement tools with explicit approval policies
- plan/quota enforcement tied to Stripe subscription state
- trial lifecycle and failed-payment handling
- GDPR export/delete/retention workflows

## Product principle

The commercial value chain is:

`Business onboarding → Product data → AI Employee → Customer channel → Conversation → Human handoff → Commerce action → Order → ROI`

New AI features should not be prioritized ahead of closing this operational loop.
