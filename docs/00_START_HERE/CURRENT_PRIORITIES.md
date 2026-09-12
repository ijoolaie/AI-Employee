# Current Priorities

**Reconciled:** 2026-09-12  
**Latest certified release candidate:** `v1.4.0-rc.4`  
**Certified commit:** `4cadd2df003d72de43546466a47e2c66062002c6`  
**Certification run:** `34693535048` — SUCCESS  
**Current mainline after documentation reconciliation:** `main` at the latest documentation commit  
**Current status:** EXTERNAL PRODUCTION GATES PENDING / DOCUMENTATION RECONCILED

## Executive priority

The exact `v1.4.0-rc.4` candidate at `4cadd2df003d72de43546466a47e2c66062002c6` passed Production Certification. Documentation reconciliation performed after that certification is intentionally recorded as a later mainline revision; certification does **not** transfer automatically to the post-certification documentation commits. Before any release promotion, run Production Certification again against the exact final release SHA.

PR #499 closed the SQLAlchemy workflow FK metadata cycle warning without weakening FK integrity. The repository-level hardening checkpoint is therefore reconciled. The next program frontier is the P0 external production boundary.

## P0 — external production gates

1. Provision and verify a real production target and immutable deployed identity.
2. Perform real backup/restore/DR and measure RPO/RTO.
3. Measure production SLO/SLI and error budget against real traffic.
4. Validate live provider integrations using production-safe credentials.
5. Certify Vendor → Reseller → Client runtime isolation/RBAC on the deployed target.
6. Execute DAST against the authenticated deployed target where applicable.
7. Obtain independent penetration-test/security-review evidence.
8. Verify production networking, TLS/ingress, perimeter and egress controls.
9. Verify external secret-manager lifecycle, rotation, revocation and recovery.
10. Rehearse HA/failure recovery against target RTO/RPO.
11. Execute incident-response and alert/on-call drills with named operators.
12. Complete ordered Vendor → Reseller → Client acceptance and final external certification (#210/#269).

## P1 — repository/productization status

The previously tracked P1 engineering/productization items are reconciled as complete or implemented:
- Data retention & lifecycle enforcement — engineering implemented; target lifecycle verification remains external.
- Human-in-the-loop reconciliation — engineering complete.
- Documentation consolidation & evidence index — this reconciliation pass complete.
- Platform operations dashboard — engineering implemented.
- Customer usage, budget & cost controls — engineering implemented; target billing/operations validation remains external.
- Cost anomaly detection & forecasting — engineering implemented.

No duplicate P1 implementation should be created unless a new concrete gap is found.

## Completed execution-boundary hardening checkpoint

- PR #464 — crash-safe Agent WorkItem → Run handoff.
- PR #465 — approval-resume enqueue race closed through outbox.
- PR #466 — Run creation/outbox failure boundary hardened with nested savepoint.
- PR #467 — WorkItem cancellation fenced at the DB boundary.
- PR #468 — workflow replay after side effects prevented.
- PR #470 — unsafe workflow child retries fail closed.
- PR #473 — workflow re-entry after child commit fenced.
- PR #475 — concurrent workflow event dispatch fenced.
- PR #477 — workflow terminal states made immutable.
- PR #479 — post-timeout/terminal workflow advancement fenced.
- PR #482 — durable WorkflowRun execution lease and bounded recovery.
- PR #486 — durable parallel-branch execution lease/recovery and optimistic ownership fencing.
- PR #487 — concurrent Run execution admission serialized with a database row lock.
- PR #499 — SQLAlchemy workflow child-identity FK DDL cycle warning eliminated with `use_alter=True`.

## Certification checkpoint

- Latest exact-SHA certified candidate: `v1.4.0-rc.4`
- Certified SHA: `4cadd2df003d72de43546466a47e2c66062002c6`
- Certification run: `34693535048` — SUCCESS
- Product Gates: 0 failures
- Post-certification documentation reconciliation: intentionally later commits; fresh certification required for the final release SHA.

## Evidence rules

- CI/internal validation = engineering/release evidence.
- Production-like certification = exact-SHA release-candidate evidence.
- Real production deployment = target evidence.
- Customer acceptance = independent acceptance evidence.
- Certification never transfers automatically across SHAs.
- Never fabricate production configuration, credentials, provider evidence or compliance certification.
- Never place secrets in GitHub issues, commits, documentation or chat.
