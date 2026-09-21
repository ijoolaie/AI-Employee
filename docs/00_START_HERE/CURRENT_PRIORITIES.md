# Current Priorities

**Reconciled:** 2026-09-21
**Current release:** `v1.4.9`
**Certified SHA:** `f1ce20c010779f5273eb5d0051da24cdd57b33f6`
**Production Certification:** Run `35575615877` — PASS
**Current status:** RELEASE CERTIFIED / EXTERNAL PRODUCTION EXECUTION PENDING

## Priority order

### P0 — Product completeness gate (must precede external commercial deployment)

The release certification is complete, but the readiness audit identified customer-facing product completeness gaps that must be closed before commercial production deployment.

1. Complete Persian/English localization across core customer-facing surfaces and verify true RTL behavior.
2. Complete the curated Employee Template catalog and template installation/customization contract.
3. Inventory operational lists/detail pages and close backend/frontend CRUD/lifecycle parity gaps.
4. Apply resource-specific lifecycle semantics: archive/deactivate/cancel/revoke instead of indiscriminate hard delete.
5. Standardize loading, empty, error, retry, success and permission-denied states.
6. Add browser-level product acceptance in both fa and en.
7. Reconcile documentation and then create a new post-v1.4.9 candidate release.
8. Re-run the required certification gates for the changed source.

Canonical audit: docs/current/PRODUCT_COMPLETENESS_GATE_2026-09-21.md.

### P1 — External production evidence

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

### P2 — Target verification

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

Broad feature expansion should remain paused. The product-completeness gate above is an explicit launch-blocking requirement identified by the readiness audit; external production evidence resumes after that gate is closed.
