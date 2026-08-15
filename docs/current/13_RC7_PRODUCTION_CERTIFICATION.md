# RC7 — Production Certification & Launch Readiness

## Scope

RC7 is the release hardening phase after RC6. It does not add a new business feature. It turns the existing SaaS surface into a repeatable, auditable release process.

## Release contract

Every feature remains subject to the project rule:

> Backend + DB/API + Frontend + relevant Dashboard/Workspace + Navigation + Onboarding + Documentation must move together.

## Added in RC7

### Security
- Security response headers on the API.
- Production configuration fails fast when debug mode, weak secrets, or fail-open rate limiting are used.
- Existing request size limits, webhook limits, tenant isolation and request IDs remain active.

### Observability and readiness
- Existing `/health` remains liveness.
- `/health/dependencies` is the readiness gate for PostgreSQL and Redis.
- Prometheus `/metrics` remains available for infrastructure monitoring.
- Docker healthchecks are used by the E2E stack.

### Automated certification
- GitHub Actions workflow: `.github/workflows/production-certification.yml`
- Backend compile, lint and tests.
- Frontend contract, unit and production build.
- Docker PostgreSQL/Redis/API/worker/beat smoke stack.
- Dependency readiness and E2E stack verification.
- Optional k6 smoke test: `ops/k6/smoke.js`.
- Environment gate: `backend/scripts/production_certification.py`.

## External integration evidence

The CI pipeline intentionally does **not** fake Shopify or Stripe success. A staging release is certified only after test-mode credentials are supplied and the following are demonstrated:

### Shopify
- OAuth install and callback.
- HMAC/state verification.
- Product/customer/order pagination.
- Webhook verification and duplicate suppression.
- Reconciliation.
- Inventory/order write-back where enabled.

### Stripe
- Test-mode checkout.
- Trial lifecycle.
- Subscription creation/update/cancellation.
- Webhook signature verification.
- Entitlement/quota enforcement after billing events.

### WhatsApp
- Provider verification.
- Inbound message → conversation → AI run.
- Outbound message delivery.
- Delivery/read status.
- Retry and duplicate handling.

## Security gate

Before public launch:

- `APP_ENV=production`
- `DEBUG=false`
- strong `SECRET_KEY`
- rate limiting enabled and fail-closed
- explicit CORS allowlist
- TLS at the edge
- database backups and restore drill
- Redis persistence/availability policy
- tenant-isolation tests
- webhook signature tests
- audit-log verification
- secret scanning in CI
- dependency vulnerability scanning

## Data protection gate

For EU launch:

- Privacy Policy
- Terms of Service
- DPA
- subprocessor list
- retention policy
- customer export/delete flow
- consent/cookie controls where applicable
- incident response process
- legal review of GDPR obligations

## Performance gate

Baseline smoke test is provided in `ops/k6/smoke.js`. Before launch, run a realistic workload against staging and record:

- p50/p95/p99 latency
- error rate
- queue depth
- database saturation
- Redis saturation
- AI provider latency
- webhook processing latency
- worker throughput

Do not promote a build if the agreed SLOs are exceeded.

## Launch checklist

- [ ] CI green on the release commit
- [ ] Alembic `upgrade head` succeeds on a clean database
- [ ] Alembic has exactly one head
- [ ] Backend tests pass with production dependencies installed
- [ ] Frontend contract/unit/build checks pass
- [ ] Docker stack smoke test passes
- [ ] Shopify staging E2E passes
- [ ] Stripe test-mode E2E passes
- [ ] WhatsApp staging E2E passes
- [ ] Human handoff E2E passes
- [ ] Customer export/delete verified
- [ ] Tenant isolation verified
- [ ] Backups and restore drill completed
- [ ] Monitoring and alerts configured
- [ ] Error tracking configured
- [ ] Security review complete
- [ ] GDPR/legal review complete
- [ ] Rollback plan tested

## Explicit status

RC7 provides the **certification machinery**. It is not itself proof that third-party staging credentials or external services have passed. Those checks must be executed in the target staging environment.
