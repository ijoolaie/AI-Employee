# Current Priorities

**Reconciled:** 2026-09-10  
**Certified release:** `v1.3.8`  
**Architecture baseline:** `V1.5 Agentic Operating Model`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`  
**Current engineering mainline:** `decde0ad333ba972a79053b3da6489f92a2648de`

## Executive priority

The project has three independent axes: Release, Architecture and Engineering. The current certified release remains frozen at `v1.3.8`; the engineering mainline has advanced substantially beyond that release through governance, concurrency, idempotency and RAG hardening.

The immediate engineering priority is to finish the remaining real hardening findings and perform the systematic execution/side-effect boundary audit. In parallel, the external production program remains blocked on real infrastructure and acceptance evidence.

## P0 — current engineering hardening

1. Complete PR #423 — NULL-safe TeamInstallation scope uniqueness.
2. Re-run the complete required gate topology on every changed HEAD and merge only with green exact-head evidence.
3. Audit runtime adapters, WorkItem/Run transitions, tool execution, credentials, outbox/provider side effects and mutable authority surfaces for remaining TOCTOU, idempotency and governance gaps.
4. Reconcile canonical documentation and evidence indexes to the exact current mainline SHA after each release-boundary change.
5. Promote the hardened mainline to a new immutable release candidate only after the audit exit criteria are satisfied.

## P0 — external production gates

1. Provision a real production target — VPS/cloud host, network, storage and DNS.
2. Configure protected production Environment inputs.
3. Deploy an exact certified release identity.
4. Verify deployed identity and service health.
5. Real backup/restore & DR drill.
6. Production SLO/SLI & error budget.
7. Live provider validation.
8. Vendor → Reseller → Client runtime isolation/RBAC.
9. DAST against deployed target.
10. Independent penetration test/security review.
11. Production networking hardening.
12. Secret management, rotation & recovery.
13. HA/failure-recovery rehearsal.
14. Incident-response drill and on-call.
15. Final external certification & customer acceptance (#210/#269).

## P1 — productization / operational completeness

The tracked P1 engineering gates remain implemented/complete where the roadmap says so. Target-environment verification remains external where applicable.

## Stage 8 engineering frontier

The governed workforce foundation is implemented on mainline, including AgentInstance lifecycle controls, Access Review freshness, delegation freshness and execution-time authority fingerprinting. The next gate is complete coverage of every execution and side-effect boundary, followed by workforce product surfaces, evaluation gates and final release evidence.

## Certified release checkpoint

- Release: `v1.3.8`
- Certified commit: `fd1e74b6b4c1701f7443efc202bad161ff19618c`
- Certification: Run `34052885700` — PASS
- Deployment attempt: Run `34060615390` — failed at SSH setup before remote deployment
- Deployment checkpoint: Issue #343
- Current mainline: `decde0ad333ba972a79053b3da6489f92a2648de` — **not certified**

## Evidence rules

- CI/internal validation = engineering/release evidence.
- Production-like certification = certified release-candidate evidence.
- Real production deployment = target evidence.
- Customer acceptance = independent acceptance evidence.
- Architecture documentation does not create a release.
- Certification never transfers automatically across SHAs.
- Never fabricate production configuration, credentials, provider evidence or compliance certification.
- Never place secrets in GitHub issues, commits, documentation or chat.
