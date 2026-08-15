# Final Staging Gate v1.0

Testing remains the final phase. This gate prepares the environment without claiming certification.

## Infrastructure
- [ ] PostgreSQL healthy
- [ ] Redis healthy
- [ ] Celery worker consuming jobs
- [ ] Celery beat/scheduler running
- [ ] Backend healthy/readiness passing
- [ ] Frontend served over TLS
- [ ] Logs and metrics visible
- [ ] Database migrations applied

## Application smoke checks
- [ ] Login
- [ ] Tenant isolation
- [ ] Create AI Employee
- [ ] Queue Run
- [ ] Inspect Trace
- [ ] Execute Workflow
- [ ] Complete Approval

## External providers
- [ ] Stripe test credentials + webhook
- [ ] Shopify test credentials + webhook
- [ ] WhatsApp test credentials + webhook
- [ ] AI provider test credentials

## Exit condition
Every item must be verified in staging before Phase 7 final testing starts. Unknown = BLOCKED.
