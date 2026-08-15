# Release Go / No-Go Checklist v1.0

## Automated gates

- [ ] Backend unit/integration suite PASS
- [ ] Frontend typecheck PASS
- [ ] Frontend lint PASS
- [ ] Frontend unit/contract suite PASS
- [ ] Frontend production build PASS
- [ ] API contract check PASS
- [ ] Critical Playwright E2E PASS

## Runtime gates

- [ ] PostgreSQL healthy
- [ ] Redis healthy
- [ ] Celery worker/beat healthy
- [ ] API health/readiness PASS
- [ ] Frontend health PASS
- [ ] Migrations applied successfully
- [ ] No migration drift

## Security gates

- [ ] Auth/RBAC PASS
- [ ] Tenant isolation PASS
- [ ] Secret scan PASS
- [ ] Webhook authentication PASS
- [ ] Rate-limit checks PASS
- [ ] Security regression suite PASS

## Integration gates

- [ ] Stripe CERTIFIED
- [ ] Shopify CERTIFIED
- [ ] WhatsApp CERTIFIED
- [ ] Email/webhook flows CERTIFIED
- [ ] Human handoff CERTIFIED

## Operations gates

- [ ] Metrics dashboard available
- [ ] Error logging available
- [ ] Alerts tested
- [ ] DLQ/replay tested
- [ ] Backup completed
- [ ] Restore completed and verified
- [ ] Rollback completed in staging
- [ ] Incident/runbook documentation complete

## Final decision

### GO only if

- No P0 blocker remains.
- All critical E2E scenarios pass.
- All claimed external integrations have evidence.
- Backup/restore and rollback have evidence.
- Product completion matrix contains no unexplained `MISSING` item in release scope.

### NO-GO if

Any critical gate is `BLOCKED`, `FAIL`, or lacks evidence.
