# Current Priorities

**Reconciled:** 2026-09-07  
**Release baseline:** `v1.3.8`  
**Architecture baseline:** `V1.5 Agentic Operating Model`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`

## Executive priority

The project now has one clear roadmap with independent Release, Architecture and Engineering axes. The immediate priority remains **real production infrastructure and external acceptance of the frozen `v1.3.8` release**.

V1.5 is the architecture baseline, not a release. Future AI workforce/company-model work is tracked separately in Stage 8+ of `docs/current/PRODUCTIZATION_ROADMAP.md` and must not be represented as implemented until built and verified.

## P0 — external production gates

1. Provision a real production target — VPS/cloud host, network, storage and DNS.
2. Configure protected production Environment inputs.
3. Deploy exact `v1.3.8` identity — `fd1e74b6b4c1701f7443efc202bad161ff19618c`.
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

The previously tracked P1 engineering gates remain implemented/complete where stated by the roadmap. Target-environment verification remains external where applicable.

## Next product frontier — Stage 8

Once the external production boundary is addressed, the next product work is the **AI Company Operating Model Foundation**:

1. Human CEO/Chairman authority model.
2. AI Board governance and decision rights.
3. AI Internal Manager.
4. Founding AI workforce and customer-facing templates.
5. Workforce lifecycle and CEO approval gate.
6. AgentDefinition / AgentTemplate / AgentInstance separation.
7. Reusable AI teams.
8. Workforce governance UX, evaluation and audit.

This is intentionally a future product stage, not a current release claim.

## Certified release checkpoint

- Release: `v1.3.8`
- Tag target: `fd1e74b6b4c1701f7443efc202bad161ff19618c`
- Certification: Run `34052885700` — PASS
- Deployment attempt: Run `34060615390` — failed at SSH setup before remote deployment
- Deployment checkpoint: Issue #343

## Evidence rules

- CI/internal validation = engineering/release evidence.
- Production-like certification = certified release-candidate evidence.
- Real production deployment = target evidence.
- Customer acceptance = independent acceptance evidence.
- Architecture documentation does not create a release.
- Certification never transfers automatically across SHAs.
- Never fabricate production configuration, credentials, provider evidence or compliance certification.
- Never place secrets in GitHub issues, commits, documentation or chat.
