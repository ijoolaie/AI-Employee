# Customer Acceptance Checklist

## Release identity

- [ ] Release version recorded
- [ ] Source commit SHA recorded
- [ ] SHA-256 checksum verified
- [ ] Migration head recorded

## Infrastructure

- [ ] PostgreSQL healthy
- [ ] Redis healthy
- [ ] API healthy
- [ ] Worker healthy
- [ ] Beat healthy
- [ ] Frontend healthy
- [ ] TLS/DNS verified

## Application

- [ ] Login works
- [ ] Customer/tenant isolation verified
- [ ] RBAC/authorization verified
- [ ] Core business workflow verified
- [ ] Background job verified
- [ ] File/storage workflow verified

## Operations

- [ ] Backup completed
- [ ] Restore evidence available
- [ ] Rollback artifact available
- [ ] Secrets checklist completed
- [ ] Monitoring/logging configured
- [ ] Support/handoff contacts recorded

## Sign-off

Customer: ____________________

Operator: ____________________

Date: ____________________

Exceptions / follow-ups: ______________________________
