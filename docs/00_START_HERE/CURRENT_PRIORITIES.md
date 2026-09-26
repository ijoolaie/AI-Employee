# Current Priorities

**Reconciled:** 2026-09-26
**Current release:** `v1.4.11`
**Certified SHA:** `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`
**Production Certification:** Run `35848311037` / Job `107139710452` — PASS
**Current status:** v1.4.11 RELEASE-CERTIFIED / LOCAL-ENGINEERING / EXTERNAL GATES OPEN

## Priority order

### P0 — Product completeness regression watch

The customer-facing product-completeness gate that preceded v1.4.11 certification has been closed for the current audited scope. Do not reopen completed work without a regression, new requirement, or newly discovered unsupported surface.

1. **DONE:** Persian/English customer operational browser acceptance, including lang=fa / dir=rtl coverage.
2. **DONE:** Employee Template catalog expanded to seven tenant-safe bilingual starter templates with lifecycle/installation metadata.
3. **DONE:** Product, Customer, Order/Invoice and Schedule lifecycle parity reviewed; resource-specific non-destructive semantics are used where retention/auditability requires them.
4. **DONE:** Customer Analytics/Reporting retry, empty-state and locale-aware formatting parity.
5. **DONE:** Governance localization cleanup and customer operational EN/FA acceptance.
6. **DONE:** Vendor/Reseller/Customer Test Center execution boundaries are edition-aware.
7. **DONE:** v1.4.11 exact-SHA certification passed with Product Gate Failures = 0.
8. **REGRESSION WATCH:** continue monitoring residual/non-core customer surfaces for localization, lifecycle, CRUD parity, permission, and UX-state regressions.

Canonical historical audit: docs/current/PRODUCT_COMPLETENESS_GATE_2026-09-21.md. Its original findings are retained as historical evidence; this file is the current priority source.

### P1 — External production evidence

External gates remain intentionally **OPEN — PENDING EXTERNAL EXECUTION** because the project is still being executed locally. They become actionable when an approved external target exists.

1. Establish the approved real production target and capture infrastructure identity.
2. Deploy the exact v1.4.11 release identity without retagging or modifying the certified snapshot.
3. Capture deployment, image and migration identity/checksums.
4. Verify production networking, TLS, ingress/egress and secret-manager lifecycle.
5. Validate live providers, billing and integrations where applicable.
6. Establish production SLI/SLO/error-budget measurements and alerts.
7. Execute real backup/restore and measure RPO/RTO.
8. Execute Vendor → Reseller → Customer actor-matrix isolation/RBAC validation.
9. Run authenticated DAST against the deployed target.
10. Complete independent security/penetration review.
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

The v1.4.11 release has passed repository engineering gates and exact-SHA Production Certification. The audited product-completeness work is closed for the current scope and remains under regression watch. External production evidence is intentionally still open because no external target exists. Broad feature expansion should remain paused unless a concrete customer requirement, regression, or external-validation finding creates a new engineering scope.
