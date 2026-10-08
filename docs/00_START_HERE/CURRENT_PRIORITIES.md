# Current Priorities

**Reconciled:** 2026-10-08
**Current release:** `v1.4.17`
**Certified SHA:** `b403c0dcdea579e017738a6fdea138c2b1a2999c`
**Current main head:** `ceefce8f43dd2479972f3c0c1629d72ebdef74e5` at the time of this reconciliation. This is post-release engineering work and is **NOT release-certified**.
**Production Certification:** v1.4.17 exact-SHA Run `37625345534` / Job `112805570856` — PASS
**W10 Internal Company Dogfood:** Run `37189332690` / Job `111398049109` — PASS
**Current status:** v1.4.17 exact-SHA certified and published / external gates OPEN

## Immediate release-candidate priorities

1. **DONE:** W16 exact-SHA Production Certification and immutable v1.4.16 release.
2. **DONE:** W10 Internal Company Dogfood on the certified SHA.
3. **DONE:** Reconcile current documentation with the certified v1.4.17 release identity.
4. **DONE:** Exact-SHA Production Certification of v1.4.17 — Run `37625345534` / Job `112805570856` — PASS.
5. **DONE:** Create and verify Git tag `v1.4.17` at exact SHA `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
6. **DONE:** Publish and verify GitHub Release `v1.4.17`.
7. **OPEN:** External production deployment, live-provider validation, security/operations evidence and customer acceptance remain separate gates.

## P0 — Published-release reconciliation

`v1.4.17` is now the latest published exact-SHA certified release.

1. **DONE:** Certified SHA = `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
2. **DONE:** Product Gate failures = 0.
3. **DONE:** Certification evidence generated and uploaded; digest = `sha256:c05d9ba79e135dfb64ffd7aed89e2fd36b1ebcb53f6ef2ddfb865e516b870e3d`.
4. **DONE:** Git tag `v1.4.17` verified against the certified SHA.
5. **DONE:** GitHub Release `v1.4.17` published.
6. **DONE:** Release identity preserved as immutable.
7. **OPEN:** External production deployment and customer acceptance remain unverified.

## P1 — External production evidence



External gates remain intentionally **OPEN — PENDING EXTERNAL EXECUTION** because the project is still being executed locally. They become actionable when an approved external target exists.

1. Establish the approved real production target and capture infrastructure identity.
2. Deploy the latest approved immutable release identity only after an external target is provisioned; the current latest certified release is `v1.4.17` at exact SHA `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
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

### P2 — Governed Workforce semantic runtime evidence

The semantic runtime evidence slice is now **IMPLEMENTED / VALIDATED** by PR #832 and is no longer an open evidence gap.

1. **DONE:** canonical Run-path Workforce role/operation/tool enforcement is implemented after PR #827.
2. **DONE:** generic real-stack Agent WorkItem E2E proves the real Tenant → Agent → WorkItem → Run → Celery → audit path.
3. **DONE:** PR #832 added only E2E-local deterministic tool-call/provider infrastructure; production provider defaults remain unchanged.
4. **DONE:** local real-stack semantic matrix executed successfully through WorkItem → Run → Celery → ToolRegistry → governed market-research handler.
5. **DONE:** matrix covered allowed execution, runtime binding correlation, wrong-role denial, stale-capability denial, approval-required denial, cross-tenant assignment denial and persisted tool.call audit evidence.
6. **DONE:** evidence index reconciled against the merged PR boundary.
7. **NEXT DECISION:** only if this post-certification scope is intentionally selected for release should a new release candidate and fresh exact-SHA certification be created.

Do not add generic wrappers, reclassify unrelated tools, or alter production provider behavior solely to manufacture evidence. Unsupported workforce operations remain intentionally denied until a real tenant-safe semantic handler and explicit binding exist.
### P3 — Target verification and externally discovered engineering scope

- Data retention/lifecycle verification on the real target.
- Usage/quota/cost-control validation on the real target.
- Customer support and operational ownership validation.
- Any concrete engineering defects discovered during external validation.

## Feature-expansion rule

Broad feature expansion remains paused unless one of the following creates a concrete engineering scope:

- customer requirement
- regression
- newly discovered unsupported surface
- external-validation finding
- explicit planned implementation slice backed by current roadmap/evidence

Stage 8/9 and future workforce work should therefore proceed only when the relevant slice is explicitly selected and evidence requirements are clear; workforce role names in architecture/roadmap documents are not evidence of active production capabilities.

## Evidence rules

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

The v1.4.11 release has passed repository engineering gates and exact-SHA Production Certification. The audited product-completeness work is closed for the current scope and remains under regression watch. External production evidence is intentionally still open because no external target exists.

The PR #955 application-code boundary is `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Its exact-SHA Production Certification has now PASSED as candidate `v1.4.17` (Run `37625345534`, Job `112805570856`). This supersedes the earlier unavailable post-merge status for the release-candidate decision. The candidate remains distinct from published `v1.4.16` until an explicit tag/release promotion is performed.



## W10 live-response checkpoint — 2026-10-03

The W10 live sales engagement loop has crossed the real-provider response boundary.

1. **DONE:** governed live SMTP send/provider acceptance — Run `37103195020` / Job `111146601368`.
2. **DONE:** live IMAP mailbox observation and Message-ID correlation.
3. **DONE:** live response ingestion.
4. **DONE:** live response idempotency replay.
5. **DONE:** live attribution `sent=1 delivered=1 responded=1`.
6. **OPEN:** independently verify customer identity/status and qualify the conversation.
7. **OPEN:** execute a governed proposal/pilot/customer-outcome path.
8. **OPEN:** independently verify a payment/revenue event.

Do **not** repeat the live SMTP certification solely to reproduce evidence already captured by Run `37103195020`. Any further live side effect must be explicitly operator-triggered and tied to a new evidence question.

The W10 technical response loop is therefore **VERIFIED**; the business/revenue outcome remains **NOT VERIFIED**.

## W10 customer-outcome checkpoint — 2026-10-05

The previously open W10 items have been split into technical mechanics versus real-world business outcome:

- **DONE:** governed customer/pilot deal state and proposal boundary.
- **DONE:** exact tenant/deal/payment correlation.
- **DONE:** verified payment → BusinessOrder → `WorkforceRevenueEvent` settlement mechanics on PostgreSQL.
- **DONE:** payment-event replay idempotency.
- **OPEN:** independently verify that a real responding party is an actual customer and qualify the conversation.
- **OPEN:** execute an authorized real proposal/pilot/customer-outcome path.
- **OPEN:** independently verify a real payment/revenue event.

The W10 E2E uses deterministic `contract-test` payment evidence only. It must not be described as real customer revenue.


## 2026-10-06 roadmap/evidence reconciliation

- Current main is `b403c0dcdea579e017738a6fdea138c2b1a2999c` (PR #955 merge).
- PR #955 exact-head validation passed before merge; GitHub currently reports no post-merge workflow runs/statuses for the merge SHA, so the merge SHA is **NOT post-merge verified**.
- W17, W18, W19, W20, W21, W22 and W23 implementation/evidence gates are closed at their documented boundaries.
- W9 QA & DevOps is **already VERIFIED on the real stack**: final Run `36891616509`, Job `110468909696`, verification commit `5887c26c727fd2681cc1dd71fc17f0a475c9e80a`. Therefore W9 must not be treated as an unimplemented next slice.
- The roadmap W9→W10 sequence remains historically correct: W9 evidence is closed; W10 is the business-validation phase. W10 technical mechanics are now real-stack verified, while real customer qualification, real customer acceptance and realized external revenue remain open.
- External/live work remains intentionally deferred to the final external-validation phase.
- Immediate engineering priority: hardening/reconciliation, not duplicate W9 implementation.


## 2026-10-08 Product Experience Decision — Local-First AI Company World

The next product-design/engineering frontier is no longer additional backend feature expansion. The product must convert the existing governed platform into a clear, attractive and commercially understandable AI Company experience.

### New product direction

1. Keep Management Mode as the conventional SaaS operating surface.
2. Add World Mode as an explorable AI Company HQ over the same authoritative backend state.
3. Use the mobile isometric office/tycoon reference as a visual and interaction benchmark, not as a source-code or formula specification.
4. Make desktop and mobile first-class through one World Engine with different input adapters.
5. Tie progression to real AI Employees, WorkItems, customers, conversations, orders, revenue, usage and capabilities.
6. Do not introduce a fake game economy, fake business activity or permission bypass through game mechanics.

### Canonical specification

`docs/blueprint/AI_COMPANY_WORLD_GAMEPLAY_SPEC.md` is the canonical product/gameplay specification for this direction.

### Immediate engineering order

- World Foundation
- Real Company projections
- Business outcome loop
- Company progression/capabilities
- Living World
- Mobile parity
- Polish/performance

### Execution boundary

The project remains local-first for this work. External production is intentionally not the current execution target. Interactive World Mode is a future implementation slice and must not be represented as implemented/certified until code and evidence exist.

## P4 — AI Company World F0-F7 local product track

**Status on main:** F0-F7 are merged by PR #963 at `ceefce8f43dd2479972f3c0c1629d72ebdef74e5`. This is engineering evidence, not a new production certification.

1. **DONE:** F0 dual-mode shell and `/world` route.
2. **DONE:** F1 isometric renderer foundation, camera, desktop/mobile input, pinch zoom and camera controls.
3. **DONE:** F2 authoritative employee projection from `/customer-dashboard/office`.
4. **DONE:** F3 employee interaction and World → Employee Management bridge.
5. **DONE:** F4 recorded business outcome loop via `/analytics/roi`.
6. **DONE:** F5 authoritative HQ tier/capacity progression presentation.
7. **DONE:** F6 live state refresh and source-freshness visibility.
8. **DONE:** F7 responsive/accessibility/presentation polish and component-boundary refactor.
9. **DONE:** PR #963 passed its required CI/security/infrastructure checks before merge.
10. **OPEN:** A local real-stack validation should be rerun for any future runtime-affecting World change; it is not retroactively implied by the merge.
11. **OPEN:** PixiJS dependency integration remains a renderer-specific follow-up. It must be introduced only with a regenerated and validated lockfile, not by hand-editing dependency metadata.

Canonical implementation record: `docs/current/AI_COMPANY_WORLD_F0_F7_IMPLEMENTATION.md`.
