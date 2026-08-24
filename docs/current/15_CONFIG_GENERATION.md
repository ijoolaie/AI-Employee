# Customer Configuration Generation

Phase 4B defines a reproducible, secret-free customer configuration template.

## Generate

```bash
python scripts/generate_customer_config.py --domain customer.example.com
```

The generated file is `dist/config/.env.customer.example` unless `--output` is supplied.

## Rules

- Never commit a populated `.env` file.
- The generator never creates real credentials.
- Generate `SECRET_KEY`, database passwords, and Redis passwords with the operator's approved secret manager or cryptographically secure local tooling.
- URL-encode passwords before embedding them in connection URLs.
- Optional paid integrations may remain empty until enabled for a customer.
- Production must use `DEBUG=false` and explicit CORS/frontend URLs.

## Required runtime inputs

Postgres credentials, `SECRET_KEY`, database URLs, Redis credentials/URLs, Celery URLs, CORS origins, frontend URLs, and `NEXT_PUBLIC_API_URL` are required by the production compose contract.

## Optional inputs

LM Studio, Anthropic, SMTP, OpenTelemetry exporter, Stripe, and Shopify credentials are optional at first install. Their empty/default behavior must remain aligned with `docker-compose.production.yml`.
