# Current Priorities

**Reconciled:** 2026-09-05
**Current engineering main baseline:** `44e1c0f339e2440bafe9f4e122d2b63dc2fc09c2`

## Executive priority

Phase 13 and Phase 14.1–14.16 engineering are complete. Production-like infrastructure validation is complete in CI. The repository has also completed the tracked P1 engineering/productization gates and the latest Stage 7 engineering contracts. The remaining program is **Stage 7 — External Production Certification & Customer Acceptance**.

The complete gap list is maintained in `docs/current/PRODUCTION_GAP_REGISTER_2026-09-04.md` and the ordered roadmap in `docs/current/PRODUCTIZATION_ROADMAP.md`.

## P0 — certification blockers

1. **Immutable release & release identity** — freeze one exact SHA/tag and provenance.
2. **External production deployment** — deploy that exact identity to the real target.
3. **Real backup/restore & DR drill** — prove target RPO/RTO.
4. **Production SLO/SLI & error budget** — measure against the target.
5. **Live provider validation** — validate real AI/email/payment/storage/provider behavior and failure modes.
6. **Vendor → Reseller → Client runtime isolation/RBAC** — complete real-stack evidence for #19.
7. **DAST** — scan the deployed running stack, triage and retest.
8. **Independent penetration test/security review** — obtain independent findings and disposition.
9. **Production networking hardening** — prove TLS, ingress, firewall and network-policy evidence.
10. **Secret management, rotation & recovery** — prove the external secret lifecycle.
11. **High availability & failure recovery** — rehearse failure/failover against recovery objectives.
12. **Incident-response drill** — execute a realistic incident scenario and capture lessons.
13. **Alert ownership & on-call escalation** — prove routing, ownership and escalation.
14. **Final external certification & customer acceptance** — ordered acceptance and final sign-off (#210/#269).

All P0 items retain their external boundary even where repository engineering contracts are already complete.

## P1 — productization & operational completeness

The following P1 engineering gates are now reconciled as implemented/complete; target-environment verification remains external where applicable:

15. **Data retention & lifecycle enforcement** — ENGINEERING IMPLEMENTED.
16. **Human-in-the-loop TODO reconciliation** — ENGINEERING COMPLETE.
17. **Documentation consolidation & evidence index** — ENGINEERING COMPLETE.
18. **Platform operations dashboard** — ENGINEERING COMPLETE via the existing `/admin/operations` surface.
19. **Customer usage, budget & cost controls** — ENGINEERING IMPLEMENTED.
20. **Cost anomaly detection & forecasting** — ENGINEERING IMPLEMENTED.

See the canonical gap register for exact evidence and remaining external boundaries.

## Completed engineering stages and checkpoints

- Stage 1 / #285 — certification-readiness and cross-platform hardening: complete.
- Stage 2 / #286 — tenant-fair scheduling and resource isolation: complete.
- Stage 3 / #287 — bounded load/stress/capacity validation: complete.
- Stage 4 / #288 — security/privacy/compliance engineering: complete.
- Stage 5 / #289 — capacity/cost/operational optimization: complete.
- Stage 6 / #290 — V1.5 Human + Agent operating model: complete.
- PR #315 — production-like infrastructure validation: merged; CI run `33884955068` passed.
- PR #320 — immutable-release build evidence: engineering complete; external registry publication/signing remains pending.
- PR #323 — HA/failure-recovery engineering rehearsal: complete; target HA/RTO/RPO evidence remains external.
- PR #324 — SLO/error-budget engineering contract: complete; live measurement remains external.
- PR #325 — provider integration preflight: complete; live provider validation remains external.
- PR #327 — alert ownership/routing contract: complete; live paging/on-call remains external.
- PR #329 — runtime isolation/RBAC CI gate: complete; external actor-matrix certification remains pending.
- PR #330 — production network hardening contract: complete; deployed perimeter evidence remains external.
- PR #331 — production secret-management contract: complete; external manager/rotation/recovery evidence remains pending.

## Evidence rules

- CI/internal load and security validation = engineering evidence.
- Local real-stack validation = local evidence.
- External production/customer acceptance = independent external evidence.
- Certification never transfers automatically across SHAs.
- Never fabricate production configuration, customer acceptance, provider evidence or compliance certification.
- P0 completion requires evidence attached to the exact immutable release identity intended for acceptance.
