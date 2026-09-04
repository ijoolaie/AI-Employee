# Current Priorities

**Reconciled:** 2026-09-04

## Executive priority

Phase 13 and Phase 14.1–14.16 engineering are complete. Production-like infrastructure validation is complete in CI. The remaining program is **Stage 7 — External Production Certification & Customer Acceptance**, plus explicitly tracked P1 productization/operational completeness items.

The complete gap list is maintained in `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md` and the ordered roadmap in `docs/current/PRODUCTIZATION_ROADMAP.md`.

## P0 — certification blockers

1. **Immutable release & release identity** — freeze one exact SHA/tag and provenance.
2. **External production deployment** — deploy that exact identity to the real target.
3. **Real backup/restore & DR drill** — prove target RPO/RTO.
4. **Production SLO/SLI & error budget** — define and measure against the target.
5. **Live provider validation** — validate real AI/email/payment/storage/provider behavior and failure modes.
6. **Vendor → Reseller → Client runtime isolation/RBAC** — complete real-stack evidence for #19.
7. **DAST** — scan the deployed running stack, triage and retest.
8. **Independent penetration test/security review** — obtain independent findings and disposition.
9. **Production networking hardening** — TLS, ingress, firewall and network-policy evidence.
10. **Secret management, rotation & recovery** — prove the external secret lifecycle.
11. **High availability & failure recovery** — rehearse failure/failover against recovery objectives.
12. **Incident-response drill** — execute a realistic incident scenario and capture lessons.
13. **Alert ownership & on-call escalation** — prove routing, ownership and escalation.
14. **Final external certification & customer acceptance** — ordered acceptance and final sign-off (#210/#269).

## P1 — productization & operational completeness

15. **Data retention & lifecycle enforcement** — reconcile policy, implementation and target verification.
16. **Human-in-the-loop TODO reconciliation** — resolve the documented approval-path TODO in `backend/app/services/run_service.py`.
17. **Documentation consolidation & evidence index** — keep canonical docs synchronized and remove stale claims.
18. **Platform operations dashboard** — complete a dedicated operational view beyond the current workspace read model.
19. **Customer usage, budget & cost controls** — extend current admin optimization/budget signals to customer operations where required.
20. **Cost anomaly detection & forecasting** — add deterministic anomaly/forecast signals with alert/audit behavior.

## Completed engineering stages

- Stage 1 / #285 — certification-readiness and cross-platform hardening: complete.
- Stage 2 / #286 — tenant-fair scheduling and resource isolation: complete.
- Stage 3 / #287 — bounded load/stress/capacity validation: complete.
- Stage 4 / #288 — security/privacy/compliance engineering: complete.
- Stage 5 / #289 — capacity/cost/operational optimization: complete.
- Stage 6 / #290 — V1.5 Human + Agent operating model: complete.
- PR #315 — production-like infrastructure validation: merged at `93c717969a192ae5b90b909c2c4e8aaa89bea50a`.

## Evidence rules

- CI/internal load and security validation = engineering evidence.
- Local real-stack validation = local evidence.
- External production/customer acceptance = independent external evidence.
- Certification never transfers automatically across SHAs.
- Never fabricate production configuration, customer acceptance, provider evidence or compliance certification.
- P0 completion requires evidence attached to the exact immutable release identity intended for acceptance.
