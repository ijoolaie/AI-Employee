# RC4 — Shopify Commerce Loop

## Goal

RC4 closes the first real commerce loop for a tenant storefront:

`Shopify → Products/Inventory → AI Employee tools → Orders/Customers → Unified Inbox`

## Implemented

- Shopify integration configuration with configurable Admin API version.
- Tenant-scoped connection test (`POST /api/v1/commerce-integrations/{id}/test`).
- Product sync (`POST /api/v1/commerce-integrations/{id}/sync/products`).
- Order + customer sync (`POST /api/v1/commerce-integrations/{id}/sync/orders`).
- Shopify products are upserted into the tenant Product Catalog using provider IDs in `attributes`.
- Shopify customers are upserted into the tenant CRM using `external_key`.
- Shopify orders are upserted into the tenant Business Orders and linked to the synced customer through order metadata.
- AI tools: `search_products`, `get_product`, `check_inventory`, `create_order`, `get_order`, `track_order`.
- Frontend Commerce Integrations screen now supports Shopify connection, connection test and product/order sync.
- Onboarding and AI Employee tool selection remain the entry points for this capability.
- Integration API responses redact provider secrets.

## Security boundary

Provider credentials are accepted only by the authenticated tenant integration endpoint and are never returned in list/create responses. Production deployments should additionally encrypt integration secrets at rest using the deployment secret/KMS strategy.

## Current connector scope

This RC uses the Shopify Admin REST API through a configurable API version and performs an initial bounded sync of up to 250 products/orders per invocation. Pagination, webhook-driven incremental sync, OAuth installation flow and write-back order creation should be completed before calling the connector production-complete.

## Required production completion

1. Shopify OAuth/install flow and least-privilege scopes.
2. Cursor/page pagination and incremental sync.
3. Webhooks for product, inventory, order and customer changes.
4. Outbound commerce action adapter (draft order/cart where permitted by Shopify permissions).
5. Secret encryption/KMS and credential rotation.
6. Connector health/last-sync alerts and retry queue.
7. Full E2E test against a dedicated Shopify development store.

## UX rule

Every new commerce option must update the relevant Backend API, Tool Registry, Product/Order/Customer screens, Integrations screen, Onboarding, AI Workspace, navigation and documentation together.
