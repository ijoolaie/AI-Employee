# Current Priorities

**Reconciled:** 2026-09-21
**Current release:** `v1.4.9`
**Certified SHA:** `f1ce20c010779f5273eb5d0051da24cdd57b33f6`
**Production Certification:** Run `35575615877` — PASS
**Current status:** RELEASE CERTIFIED / EXTERNAL PRODUCTION EXECUTION PENDING

## Priority order

### P0 — External production evidence

1. Establish the approved real production target and capture its infrastructure identity.
2. Deploy the exact `v1.4.9` release identity without retagging or modifying the certified snapshot.
3. Capture deployment, image and migration identity/checksums.
4. Verify production networking, TLS, ingress/egress and secret-manager lifecycle.
5. Validate live providers, billing and integrations where applicable.
6. Establish production SLI/SLO/error-budget measurements and alerts.
7. Execute real backup/restore and measure RPO/RTO.
8. Execute Vendor → Reseller → Client actor-matrix isolation/RBAC validation.
9. Run authenticated DAST against the deployed target.
10. Complete independent security/pentest review.
11. Rehearse HA/failure recovery and rollback.
12. Execute incident-response and staffed on-call drill.
13. Complete Vendor, then Reseller, then Customer acceptance.
14. Reconcile residual risks and execute the final commercial go-live gate.

### P1 — Target verification

- Data retention/lifecycle verification on the real target.
- Usage/quota/cost-control validation on the real target.
- Customer support and operational ownership validation.
- Any concrete engineering defects discovered during external validation.

### Evidence rules

- CI/internal validation = engineering evidence.
- Exact-SHA certification = release evidence.
- Real deployment = target evidence.
- Provider validation = environment/provider evidence.
- Security testing = security evidence.
- DR/restore rehearsal = resilience evidence.
- Customer acceptance = independent acceptance evidence.
- No evidence transfers automatically across SHAs.
- Documentation cannot substitute for missing operational evidence.
- Never fabricate infrastructure, provider, security, DR or acceptance evidence.

## Current engineering state

The v1.4.9 release has passed repository engineering gates and exact-SHA Production Certification. Do not restart completed test suites without a regression trigger. Do not restart completed test suites without a regression trigger.

Broad feature expansion should remain paused unless the readiness audit identifies a genuine launch-blocking product requirement.
