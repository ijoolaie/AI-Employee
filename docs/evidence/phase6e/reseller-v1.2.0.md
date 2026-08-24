# Phase 6E Reseller Production Evidence — v1.2.0

Status: **TEMPLATE — NOT PRODUCTION EVIDENCE**

> Replace this template only with evidence from a real Reseller environment. Never add secrets, tokens, passwords or private keys.

## Identity

```text
environment_id =
edition = reseller
release_version = v1.2.0
source_commit_sha = c329929f1c7e972f626b7ee749c8a2f05a85eace
artifact_sha256 = c8140f83d7d6c1c2e9547a9173349036b0c58ec6b229235142bc3a46dabcd484
delivery_revision = 1
deployment_timestamp_utc =
operator =
```

## Entry / Installation

- [ ] Vendor environment accepted first.
- [ ] Reseller checksum verified.
- [ ] Vendor authorization/delegation record exists.
- [ ] Reseller configuration uses only reseller-owned secrets.
- [ ] Services started and health verified.
- [ ] Migration compatibility verified; migration head recorded.

## Reseller Authority Acceptance

- [ ] Reseller can manage only its authorized scope.
- [ ] Reseller can provision authorized customers.
- [ ] Reseller cannot perform Vendor-global administration.
- [ ] Entitlement delegation cannot exceed Vendor ceiling.
- [ ] Privileged actions are audited.
- [ ] Vendor escalation path is operational.

## Monitoring / Security / Recovery

- [ ] Health monitoring active.
- [ ] Error alerting tested.
- [ ] TLS/security settings verified.
- [ ] Secrets externalized.
- [ ] Production backup completed.
- [ ] Restore/recovery drill completed.

Evidence references:

```text
monitoring =
security =
backup =
recovery =
```

## Handoff

- [ ] Release identity delivered.
- [ ] Artifact checksum delivered.
- [ ] Configuration/secret ownership documented.
- [ ] Backup/restore instructions delivered.
- [ ] Rollback/recovery instructions delivered.
- [ ] Customer provisioning responsibilities documented.
- [ ] Vendor support/escalation path confirmed.
- [ ] Operator acceptance recorded.

## Final decision

**Production acceptance: NOT YET RECORDED**

Acceptance authority:

```text
name =
date_utc =
sign-off reference =
```
