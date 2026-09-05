# Production Gap Register — 2026-09-04

> Canonical gap register. Repository/CI evidence is explicitly separated from external production certification.

## P0 gaps

1. External Production Infrastructure Deployment — **OPEN / EXTERNAL**
2. Real Backup / Restore / DR Drill — **OPEN / EXTERNAL**. Repository has production-like PostgreSQL backup + isolated restore evidence.
3. Production SLO + Error Budget — **OPEN / EXTERNAL**
4. Live Provider Integration Validation — **OPEN / EXTERNAL**
5. Vendor → Reseller → Client Runtime Evidence — **OPEN / EXTERNAL**
6. Dynamic Security Testing — **ENGINEERING CAPABILITY IMPLEMENTED; EXTERNAL TARGET OPEN**. Ephemeral OWASP ZAP validation exists in CI.
7. Independent Penetration Test — **OPEN / EXTERNAL**
8. Production Networking Hardening — **ENGINEERING CONTROLS IMPLEMENTED; EXTERNAL NETWORK HARDENING OPEN**. Production configuration rejects insecure HTTP origins and local dependency endpoints; real ingress/TLS/firewall/private-network evidence remains environment-specific.
9. Secret Management & Rotation — **ENGINEERING GUARDRAILS IMPLEMENTED; EXTERNAL SECRET STORE/ROTATION OPEN**. Production requires a strong secret and does not accept the default key; actual secret-manager integration and rotation/recovery must be validated in the target environment.
10. High Availability / Failure Recovery Architecture — **ENGINEERING REHEARSAL IMPLEMENTED; EXTERNAL HA/FAILOVER OPEN**. CI exercises restart/recovery of the production-like Compose stack, including API, worker, beat, Redis and PostgreSQL dependency recovery. This is not multi-node HA or managed-database failover evidence.
11. Incident Response Drills — **RUNBOOK + CI CONTRACT IMPLEMENTED; REAL OPERATIONAL DRILL OPEN**
12. Alert Ownership & On-Call Escalation — **OPEN / EXTERNAL**
13. Data Retention & Lifecycle Management — **ENGINEERING IMPLEMENTED; PROVIDER-SIDE BACKUP/OBJECT LIFECYCLE OPEN**
14. Release Management & Immutable Release Process — **ENGINEERING EVIDENCE IMPLEMENTED; EXTERNAL REGISTRY/ATTESTATION OPEN**
15. External Production Certification & Customer Acceptance — **OPEN / EXTERNAL**
16. Human-in-the-Loop TODO Reconciliation — **ENGINEERING COMPLETE**
17. Documentation Consolidation — **ENGINEERING COMPLETE**
18. Platform Operations Dashboard — **ENGINEERING COMPLETE**
19. Customer Usage & Cost Controls — **ENGINEERING IMPLEMENTED; TARGET BILLING VALIDATION OPEN**
20. Cost Anomaly Detection & Forecasting — **ENGINEERING IMPLEMENTED; PRODUCTION BASELINE VALIDATION OPEN**

## Failure-recovery evidence boundary

`docs/current/PHASE_14_FAILURE_RECOVERY_EVIDENCE.md` defines the CI rehearsal scope and explicitly prevents restart smoke evidence from being represented as production HA/failover certification.
