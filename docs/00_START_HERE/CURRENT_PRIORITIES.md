# Current Priorities

**Reconciled:** 2026-09-10  
**Latest certified release:** `v1.3.8`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`  
**Current mainline:** `b2e2517ce0a38dc4fecd97c047328f703bdd7de6`  
**Current release candidate:** `v1.4.0-rc.1`

## Executive priority

The project is currently in **release-candidate validation**. The latest mainline candidate `v1.4.0-rc.1` is not yet certified because one Product Gate remains blocked: **Unified WorkItem Agent real-stack**.

The previous `v1.3.8` release remains the latest certified and frozen release. Certification evidence never transfers automatically across SHAs.

## P0 — current release blocker

1. Root-cause the `Unified WorkItem Agent real-stack` certification failure.
2. Trace the complete path: Agent WorkItem → assignment → AgentExecutionAdapter → Run creation → queue dispatch → Run execution → governance/license checks → terminal state → certification assertion.
3. Correct the production path or certification assertion according to the actual root cause; do not mask the failure with an unconditional retry.
4. Run all required CI/security/architecture gates on the exact corrected HEAD.
5. Merge only after the required gates are green.
6. Rerun Production Certification with the exact corrected SHA and release version.
7. Require zero failed Product Gates before declaring the new release certified.

## Latest certification evidence

- Release candidate: `v1.4.0-rc.1`
- Target SHA: `b2e2517ce0a38dc4fecd97c047328f703bdd7de6`
- Production Certification run: `34497132748`
- Certification job: `102938351658`
- Result: **BLOCKED — 1 Product Gate failed**
- Failed gate: **Unified WorkItem Agent real-stack**
- Commercial-license fixture: **PASS**
- Failure message: empty assertion message
- Human WorkItem real-stack: **PASS**

## P1 — external production gates

After release certification is complete, the remaining external boundary still requires:

1. Provision a real production target — VPS/cloud host, network, storage and DNS.
2. Configure protected production Environment inputs.
3. Deploy the exact newly certified release identity.
4. Verify deployed identity and service health.
5. Real backup/restore & DR drill.
6. Production SLO/SLI & error budget.
7. Live provider validation.
8. Vendor → Reseller → Client runtime isolation/RBAC.
9. DAST against the deployed target where applicable.
10. Independent penetration test/security review.
11. Production networking hardening.
12. Secret management, rotation & recovery.
13. HA/failure-recovery rehearsal.
14. Incident-response drill and on-call.
15. Final external certification & customer acceptance.

## Certified release checkpoint

- Release: `v1.3.8`
- Tag target: `fd1e74b6b4c1701f7443efc202bad161ff19618c`
- Certification: Run `34052885700` — PASS
- Deployment attempt: Run `34060615390` — failed before remote deployment
- Deployment checkpoint: Issue #343

## Stage 8 frontier

AI Company Operating Model / workforce-governance work remains a product frontier and must not be confused with release certification status.

## Evidence rules

- CI/internal validation = engineering/release evidence.
- Production-like certification = exact-SHA release-candidate evidence.
- Real production deployment = target evidence.
- Customer acceptance = independent acceptance evidence.
- Architecture documentation does not create a release.
- Certification never transfers automatically across SHAs.
- Never fabricate production configuration, credentials, provider evidence or compliance certification.
- Never place secrets in GitHub issues, commits, documentation or chat.
