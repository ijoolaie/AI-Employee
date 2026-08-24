# Phase 6E — Production Delivery Runbook & Evidence Contract

## Purpose

Phase 6E is the external production-delivery gate for the three edition profiles produced by Phase 6D.

It proves that the immutable Vendor release can be installed and operated as three real environments without weakening the Vendor → Reseller → Customer authority hierarchy.

This document is an execution runbook and evidence contract. It does **not** claim that a production environment exists until environment-specific evidence is attached.

## Release under test

Default candidate release:

```text
release_version = v1.2.0
source_commit_sha = c329929f1c7e972f626b7ee749c8a2f05a85eace
migration_head = p5license02
```

The release identity MUST be immutable for a given delivery record. A new source SHA requires a new release record.

## Environment sequence

Production delivery is performed in this order:

1. **Vendor** — establish the authoritative control plane first.
2. **Reseller** — provision only through Vendor-authorized delegation.
3. **Customer** — provision only through the authorized upstream path.

Do not deploy Reseller or Customer as isolated copies before the Vendor authority path is validated.

## 6E-A — Vendor environment

### Entry criteria

- [ ] Release artifact downloaded from the approved release evidence.
- [ ] Runtime SHA-256 independently verified.
- [ ] Vendor edition SHA-256 independently verified.
- [ ] Production secrets supplied through the approved external secret mechanism.
- [ ] DNS/TLS and firewall requirements satisfied.
- [ ] PostgreSQL and Redis production endpoints prepared.
- [ ] Backup destination and retention policy configured.
- [ ] Monitoring/alerting destination configured.

### Installation

- [ ] Verify artifact checksum.
- [ ] Generate environment configuration without committing secrets.
- [ ] Validate production Compose configuration.
- [ ] Start dependencies and application services.
- [ ] Run `alembic upgrade head` using the release's migration graph.
- [ ] Record the resulting migration head.
- [ ] Verify API/frontend health endpoints.

### Vendor acceptance

- [ ] Vendor authentication works.
- [ ] Vendor can inspect platform health.
- [ ] Vendor can issue/revoke a downstream license.
- [ ] Audit records are generated for privileged actions.
- [ ] Tenant/RBAC boundaries are enforced.
- [ ] No Vendor secret is present in the distributable artifact.

## 6E-B — Reseller environment

### Entry criteria

- [ ] Vendor environment is accepted.
- [ ] Reseller artifact checksum is independently verified.
- [ ] Reseller configuration uses only reseller-owned secrets.
- [ ] Vendor authorization/delegation record exists.

### Installation and provisioning

- [ ] Install the exact approved Reseller revision.
- [ ] Verify migration compatibility with the Vendor release.
- [ ] Provision reseller identity through the supported control-plane path.
- [ ] Configure reseller quota/entitlement ceiling.
- [ ] Configure monitoring and backups.

### Reseller acceptance

- [ ] Reseller can manage only its authorized scope.
- [ ] Reseller can provision authorized customers.
- [ ] Reseller cannot perform Vendor-global administration.
- [ ] Entitlement delegation cannot exceed Vendor ceiling.
- [ ] Audit trail records reseller privileged actions.
- [ ] Support escalation to Vendor is operational.

## 6E-C — Customer environment

### Entry criteria

- [ ] Vendor environment is accepted.
- [ ] Reseller path is accepted where applicable.
- [ ] Customer artifact checksum is independently verified.
- [ ] Customer-owned secrets are supplied externally.
- [ ] Customer backup destination and monitoring are configured.

### Installation and provisioning

- [ ] Install the exact approved Customer revision.
- [ ] Verify migration compatibility with the Vendor release.
- [ ] Provision customer tenant through the authorized upstream path.
- [ ] Apply customer RBAC and entitlements.
- [ ] Configure backups, monitoring and alerting.

### Customer acceptance

- [ ] Customer can access only its own tenant scope.
- [ ] Customer cannot provision downstream tenants.
- [ ] Customer cannot access Vendor/Reseller control-plane operations.
- [ ] Customer entitlement checks are enforced.
- [ ] Audit records are available for privileged actions.
- [ ] Support escalation path is documented and tested.

## 6E-D — Operational evidence

Each environment MUST have an evidence record containing:

```text
environment_id
edition
release_version
source_commit_sha
artifact_sha256
deployment_timestamp_utc
migration_head
hostname_or_service_identifier
operator
health_check_result
backup_check_result
monitoring_check_result
security_check_result
recovery_check_result
handoff_status
```

Do not store passwords, tokens, private keys or other secret values in the evidence record.

## 6E-E — Recovery evidence

For each real environment:

- [ ] Confirm a known-good backup exists before destructive testing.
- [ ] Exercise the documented failure/recovery procedure.
- [ ] Confirm service health after recovery.
- [ ] Confirm database migration state after recovery.
- [ ] Record elapsed recovery time and outcome.
- [ ] Record rollback/recovery artifact identity.

A local rehearsal cannot substitute for production-target evidence.

## 6E-F — Security evidence

For each environment:

- [ ] TLS is active and certificate validation succeeds.
- [ ] Debug/development settings are disabled.
- [ ] CORS and trusted-host policy match the environment.
- [ ] Production credentials are externalized.
- [ ] Logs do not contain secrets.
- [ ] Backups are access-controlled.
- [ ] Administrative access is restricted and auditable.

## 6E-G — Handoff evidence

A delivery is not complete until the receiving operator has:

- [ ] exact release identity;
- [ ] artifact checksums;
- [ ] configuration/secret ownership instructions;
- [ ] installation result;
- [ ] migration result;
- [ ] backup/restore instructions;
- [ ] rollback/recovery instructions;
- [ ] monitoring/alert contacts;
- [ ] support/escalation path;
- [ ] acceptance sign-off.

## Evidence record template

Create one file per real environment under `docs/evidence/phase6e/` using:

```text
<environment-id>-<edition>-v1.2.0.md
```

The record MUST reference evidence, not merely state that a step passed.

## Exit criteria

Phase 6E can be marked **COMPLETE** only when all three real environment paths have environment-specific evidence for:

1. installation and health;
2. migration state;
3. security posture;
4. monitoring/alerting;
5. backup/recovery;
6. edition-specific authority boundaries;
7. operator handoff and acceptance.

Until then the correct status is:

**Phase 6E — READY FOR EXTERNAL EXECUTION.**

## Evidence boundary

GitHub Actions release validation proves artifact reproducibility and packaging integrity. It does not prove deployment to a real Vendor, Reseller or Customer environment. Production certification must remain environment-specific.
