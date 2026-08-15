# RC5 — Shopify OAuth/Webhooks + Billing Plans, Quotas & Trial

## Scope

RC5 closes the next commercial loop on top of RC4. It adds:

- Shopify Admin GraphQL connector using OAuth for merchant installation.
- Shopify HMAC-verified webhook receiver and durable delivery de-duplication.
- Cursor-paginated product/customer/order reconciliation.
- Manual reconciliation endpoint and UI.
- 14-day tenant trial with explicit `trial_ends_at` state.
- Stripe Checkout subscription trial configuration.
- Billing entitlements endpoint and Billing UI usage meters.
- Plan/quota enforcement remains provider-neutral and is applied before Run execution.

Shopify's current guidance says new public apps should use the GraphQL Admin API; REST Admin API is legacy for this purpose.

Shopify webhooks are near-real-time change notifications, but Shopify recommends reconciliation because webhook delivery is not guaranteed and event ordering is not guaranteed. RC5 therefore treats webhooks as change signals and keeps reconciliation as the consistency mechanism.

Webhook deliveries are verified with `X-Shopify-Hmac-SHA256` and de-duplicated using `X-Shopify-Webhook-Id`.

## Shopify production configuration

Set:

- `SHOPIFY_CLIENT_ID`
- `SHOPIFY_CLIENT_SECRET`
- `SHOPIFY_REDIRECT_URI`
- `SHOPIFY_SCOPES`
- `SHOPIFY_API_VERSION=2026-07`

Use the smallest scopes required by the features enabled for the merchant. Order data access may require additional Shopify approval/scopes depending on the app and data age.

## Shopify UI contract

`/integrations` now supports:

1. OAuth installation.
2. Connection test.
3. Product sync.
4. Order sync.
5. Full reconciliation.

The raw Admin API token form remains available for development/private-store testing, but production onboarding should prefer OAuth.

## Billing

New tenants start in `trialing` status for 14 days. `trial_ends_at` is persisted on the subscription. When the trial expires, entitlement checks fail closed until the tenant has an active paid subscription.

Billing UI now exposes:

- Current plan.
- Trial end date.
- Runs used / plan limit.
- AI tokens used / plan limit.
- Employees used / plan limit.
- Workflows used / plan limit.
- Stripe Checkout for paid plans.
- Stripe Billing Portal for existing Stripe customers.

## Release rule

Every new option must update all relevant layers together:

Backend model/service/API → migration → frontend page/navigation/dashboard → onboarding → documentation → verification.

## Verification boundary

This environment can statically compile Python and validate frontend source contracts, but a full production OAuth/webhook/Stripe test requires real provider credentials and network access to Shopify/Stripe. Do not mark the release production-certified until those external flows are exercised in a staging shop/account.
