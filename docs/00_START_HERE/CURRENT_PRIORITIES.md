# Current Priorities

**Reconciled:** 2026-09-20
**Current release:** `v1.4.7`
**Certified SHA:** `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
**Production Certification:** Run `35498984521` — PASS / 0 Product Gate failures
**Current status:** ENGINEERING/RELEASE CERTIFIED / EXTERNAL PRODUCTION EXECUTION PENDING

## Priority order

### P0 — External production evidence

1. Deploy the exact accepted v1.4.7 release identity to the approved real target.
2. Capture deployment, image and migration identity/checksums.
3. Verify production networking, TLS, ingress/egress and secret-manager lifecycle.
4. Validate live providers, billing and integrations where applicable.
5. Establish production SLI/SLO/error-budget measurements and alerts.
6. Execute real backup/restore and measure RPO/RTO.
7. Execute Vendor → Reseller → Client actor-matrix isolation/RBAC validation.
8. Run authenticated DAST against the deployed target.
9. Complete independent security/pentest review.
10. Rehearse HA/failure recovery and rollback.
11. Execute incident-response and staffed on-call drill.
12. Complete Vendor, then Reseller, then Customer acceptance.
13. Reconcile residual risks and execute the final commercial go-live gate.

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

The v1.4.7 release has already passed repository engineering gates and exact-SHA Production Certification. Do not restart completed test suites without a regression trigger.

Broad feature expansion should remain paused unless the readiness audit identifies a genuine launch-blocking product requirement.
