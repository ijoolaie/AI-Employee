# Compatibility Matrix

This matrix is the release acceptance baseline. Exact supported versions must be pinned/updated when the release is certified.

| Component | Baseline | Validation |
|---|---|---|
| Docker Engine | Current supported stable release | `docker version` |
| Docker Compose | Compose v2 | `docker compose version` |
| PostgreSQL | 16 | production compose image |
| Redis | 7 | production compose image |
| Backend Python | 3.12 | CI/runtime image |
| Frontend Node | 22.x | CI/runtime image |
| Browser E2E | Playwright-supported Chromium | certification workflow |
| Linux host | 64-bit Linux recommended | installation gate |

## Release rules

- Do not upgrade a foundational runtime independently of a release review.
- Any change to Postgres/Redis/Python/Node major versions requires CI and production certification evidence.
- Record the exact image/runtime versions used for a customer deployment.
- External integrations such as Stripe, Shopify, SMTP and AI providers have separate compatibility/credential requirements.
