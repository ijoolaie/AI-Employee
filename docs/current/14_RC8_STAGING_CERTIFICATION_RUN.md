# RC8 — Staging Certification Run

## Purpose

This release is a staging-certification run, not a feature release. It records what was executed in the current environment and separates local evidence from checks that require provisioned staging infrastructure and third-party test credentials.

## Release contract

Every feature remains subject to: Backend + DB/API + Frontend + relevant Dashboard/Workspace + Navigation + Onboarding + Documentation.

## Executed in the handoff environment

| Check | Result | Evidence |
|---|---|---|
| ZIP extraction/integrity | PASS | Archive extracted successfully |
| Backend Python compile | PASS | `python -m compileall -q backend/app backend/scripts` |
| Production environment gate | BLOCKED | DATABASE_URL, REDIS_URL, SECRET_KEY are not provisioned in this environment |
| Docker stack | BLOCKED | Docker executable is unavailable |
| Frontend dependency install | BLOCKED | `npm install` exceeded the available execution window |
| Frontend production build | NOT RUN | Dependency install did not complete |
| Shopify E2E | BLOCKED | Requires staging Shopify app/store credentials |
| Stripe E2E | BLOCKED | Requires Stripe test-mode credentials/webhook secret |
| WhatsApp E2E | BLOCKED | Requires provider/Meta staging credentials |
| Restore drill | NOT RUN | Requires staging database/object-storage backup |

## Required staging variables

At minimum:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- `SHOPIFY_CLIENT_ID`
- `SHOPIFY_CLIENT_SECRET`
- `SHOPIFY_SCOPES`
- `SHOPIFY_WEBHOOK_SECRET`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_STARTER`
- `STRIPE_PRICE_BUSINESS`
- `STRIPE_PRICE_PRO`
- WhatsApp provider credentials/configuration

Secrets must be supplied through the CI/staging secret manager, never committed to the repository.

## Mandatory end-to-end scenario

1. Create a tenant and owner account.
2. Start a trial.
3. Complete onboarding.
4. Install/connect a Shopify staging store through OAuth.
5. Sync products, customers and orders.
6. Publish an AI Sales Employee.
7. Open the public chat/widget.
8. Ask for a product recommendation.
9. Verify live inventory is used.
10. Add the selected product to cart / create an order where the configured connector permits it.
11. Trigger a human handoff.
12. Reply from Unified Inbox.
13. Verify CRM customer profile and order history.
14. Send/receive the same customer flow through WhatsApp.
15. Verify AI attribution and ROI analytics.
16. Exercise a plan quota.
17. Upgrade through Stripe test mode.
18. Verify entitlement changes after the Stripe webhook.
19. Export customer data.
20. Anonymize/delete the test customer and verify audit evidence.

## Promotion gate

No public launch until all mandatory external checks are PASS and the release checklist in `docs/current/13_RC7_PRODUCTION_CERTIFICATION.md` is complete.

## Current conclusion

The application code is ready for a **staging certification run**, but this environment cannot honestly certify the external integrations because the required infrastructure and credentials are unavailable. No external integration is marked PASS without evidence.
