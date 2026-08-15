# Production Operations

This directory contains release-time operational artifacts. These scripts are **not executed automatically** and require an operator-approved production environment.

## Required secrets

Provide these through a secret manager or CI environment, never commit them:

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `CORS_ORIGINS`
- Stripe secrets/webhook secret
- Shopify client credentials
- Anthropic/AI provider secrets
- provider/channel webhook secrets

## Readiness sequence

1. Provision PostgreSQL and Redis.
2. Run migrations.
3. Start API, worker and beat.
4. Confirm `/health` and `/health/dependencies`.
5. Start frontend.
6. Confirm HTTPS and security headers.
7. Enable monitoring/alerts.
8. Take a pre-release backup.
9. Execute the final verification phase.
10. Record the release evidence before promotion.
