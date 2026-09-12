# Production Server Baseline

**Reconciled:** 2026-09-12
**Status:** OPERATING BASELINE / INFRASTRUCTURE PENDING

This document defines the recommended infrastructure baseline for external production execution. It is a planning and deployment contract, not evidence that a production server has been provisioned or verified.

## 1. Recommended production profiles

| Profile | vCPU | RAM | NVMe/SSD | Purpose |
|---|---:|---:|---:|---|
| Test / staging | 4 | 8 GB | 100 GB | Integration and pre-production validation |
| Standard production | 8 | 16 GB | 150–200 GB | Initial real deployment and normal workload |
| Serious / growth | 12–16 | 32 GB | 250 GB+ | Higher concurrency, workers, observability and growth |

**Recommended starting point:** 8 vCPU, 16 GB RAM, 150–200 GB NVMe/SSD, Ubuntu 24.04 LTS, public network access with a fixed IP, and automated daily backups.

GPU is not required for the baseline when inference uses a remote provider. A GPU becomes relevant when local model inference or GPU-dependent OCR is intentionally deployed.

## 2. Host requirements

- Ubuntu 24.04 LTS or an equivalent supported Linux distribution.
- Docker Engine / Docker Compose or the repository's supported container runtime.
- Persistent SSD/NVMe storage; avoid ephemeral disks for application state.
- TLS termination and a controlled ingress/reverse proxy.
- Firewall with least-privilege inbound rules.
- Outbound egress restricted according to provider/integration requirements.
- Time synchronization enabled.
- Centralized logs/metrics and alert delivery.
- Encrypted backups stored outside the primary host/failure domain.

## 3. Production topology target

```text
Internet
   |
   v
TLS / Ingress / Firewall
   |
   +-----------------------+
   |                       |
   v                       v
Web / API               Worker(s)
   |                       |
   +-----------+-----------+
               |
               v
        PostgreSQL / durable state
               |
       +-------+--------+
       |                |
       v                v
  Backup/DR        Observability

External providers / integrations
             ^
             |
       controlled egress
```

The initial deployment does not require Kubernetes. A hardened single-host or small multi-service Docker deployment is sufficient for the first external target, provided backups, recovery, secrets, monitoring and failure procedures are independently verified.

## 4. Secrets and identity

Production secrets must live in the deployment environment or an external secret manager, never in Git, release archives, issues or documentation.

Required categories include:

- database credentials;
- application signing/authentication secrets;
- provider API credentials;
- webhook secrets;
- TLS/private-key material;
- backup credentials;
- deployment/SSH credentials.

Secrets must have ownership, rotation, revocation and recovery procedures. The deployed identity must be bound to one immutable release SHA/tag.

## 5. Minimum production evidence

A server is not considered production-verified merely because the application starts. The external evidence pack must demonstrate:

1. immutable deployed release identity;
2. health/readiness and smoke tests;
3. TLS/ingress and network controls;
4. database durability;
5. backup creation and restore test;
6. measured RPO/RTO;
7. production SLO/SLI and alerting;
8. live provider connectivity;
9. Vendor → Reseller → Client isolation/RBAC;
10. authenticated DAST where applicable;
11. failure/recovery rehearsal;
12. incident-response and on-call drill.

## 6. Capacity progression

Start with the Standard production profile unless measured workload requires otherwise. Scale vertically first when operationally simpler, then introduce additional workers/hosts as queue depth, latency, CPU, memory, database load or availability requirements justify it.

Capacity decisions must be based on measured workload and SLOs rather than server size alone.

## 7. Non-claims

This baseline does **not** mean:

- a server has been purchased or provisioned;
- production deployment has succeeded;
- live providers have been validated;
- RPO/RTO has been measured;
- external security testing is complete;
- customer acceptance is complete.

Those claims require target-specific evidence.
