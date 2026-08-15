# RC8 — Frontend Contract Hardening

## Change

The frontend package version is now `1.0.0-rc.8`, matching the RC8 release line.

The frontend contract suite now explicitly covers the RC8 customer-facing surface:

- Privacy/GDPR page and export/delete API bindings
- Customers workspace
- Unified Inbox and human reply API binding
- Customer channels workspace
- Public chat route and public message API binding
- Product API surface used by the customer experience

## Verification

The frontend contract suite was executed from the repository root with:

```text
node frontend/scripts/test-frontend-contract.mjs
```

Result:

```text
127 passed, 0 failed
```

The existing backend baseline remains unchanged: the previously verified Docker stack has 150 backend tests passing.

## Next gate

Run the full Docker build and backend suite, then run the frontend production build. External Shopify, Stripe and WhatsApp certification still requires staging credentials and infrastructure.
