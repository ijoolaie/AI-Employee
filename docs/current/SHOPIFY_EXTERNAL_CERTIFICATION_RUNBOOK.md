# P1 Shopify External Certification Runbook

## Purpose

This runbook closes the P1 Shopify external-provider gate against a free Shopify development store. It validates OAuth installation, Admin GraphQL connectivity, webhook registration/delivery, idempotent webhook recording, and reconciliation.

Shopify development stores are intended for app development/testing and can be created from the Dev Dashboard. They support test orders without real payment transactions.

## 1. Create the free test environment

1. Open the Shopify Dev Dashboard.
2. Create a **development store** from **Stores → Create store**.
3. Enable generated test data when creating the store.
4. Create an app in the same Shopify organization.
5. Configure the app's OAuth redirect URI to the value of `SHOPIFY_REDIRECT_URI` in the deployment environment.
6. Copy the app **Client ID** and **Client Secret** into the runtime environment as `SHOPIFY_CLIENT_ID` and `SHOPIFY_CLIENT_SECRET`.

Never commit the client secret. Shopify uses the app secret to authenticate webhook signatures.

## 2. Runtime configuration

For a local production-like run:

```env
SHOPIFY_CLIENT_ID=<dev-dashboard-client-id>
SHOPIFY_CLIENT_SECRET=<dev-dashboard-client-secret>
SHOPIFY_REDIRECT_URI=http://localhost:8000/api/v1/commerce-integrations/shopify/callback
SHOPIFY_SCOPES=read_products,read_inventory,read_orders,read_customers,write_orders
SHOPIFY_API_VERSION=2026-07
FRONTEND_APP_URL=http://localhost:3000
```

For a remotely reachable environment, use an HTTPS callback URL.

## 3. Execute OAuth

With the backend running, authenticate as a tenant and open:

```text
GET /api/v1/commerce-integrations/shopify/install?shop=<dev-store>.myshopify.com
```

Expected result:

- Shopify installation/authorization page opens.
- OAuth callback returns to the configured application.
- A tenant-scoped Shopify integration is created or updated.
- The stored configuration contains the shop domain, access token, scope, API version, and `oauth_installed=true`.
- Webhook registration is attempted automatically.

## 4. Connectivity test

Use the returned integration ID:

```text
POST /api/v1/commerce-integrations/<integration-id>/test
```

Expected result: `connected=true` and the Shopify shop identity is returned.

## 5. Reconciliation

Run:

```text
POST /api/v1/commerce-integrations/<integration-id>/reconcile
```

Expected result:

- products are read from Shopify and upserted locally;
- customers are read and upserted locally;
- orders are read and upserted locally;
- repeated reconciliation reports updates rather than duplicate records.

## 6. Webhook certification

Create a test order in the development store. Shopify's development environment can emit the corresponding order webhook immediately.

Verify:

1. `X-Shopify-Hmac-Sha256` is accepted only when signed with the app secret.
2. `X-Shopify-Webhook-Id` is recorded.
3. The webhook event is persisted once.
4. Replaying the same webhook ID returns `duplicate=true` and does not create a second event.
5. The response is HTTP 200 for a valid delivery.

The application currently registers product, order, customer, and inventory webhook topics during OAuth callback.

## 7. Evidence to attach to P1

Record these artifacts without storing secrets:

- dev-store domain (non-secret);
- OAuth success timestamp;
- integration ID;
- successful `test` response with shop ID/name/domain;
- reconciliation response with counts;
- webhook delivery timestamp/topic/webhook ID;
- duplicate replay result;
- final tenant-isolation check;
- commit SHA of the certified application revision.

Do **not** attach client secrets, access tokens, authorization codes, or raw authenticated request headers.

## Pass criteria

| Gate | Required evidence |
| --- | --- |
| OAuth | callback completes and integration is persisted for the correct tenant |
| GraphQL | shop identity query succeeds |
| Reconciliation | products/customers/orders sync successfully and is idempotent |
| Webhook authenticity | invalid HMAC rejected; valid HMAC accepted |
| Webhook idempotency | duplicate webhook ID is not inserted twice |
| Tenant isolation | integration cannot be accessed through another tenant context |

A successful run certifies the **Shopify external test environment**. It does not certify a production Shopify merchant deployment.
