# Current Priorities

**Reconciled:** 2026-10-07
**Current release:** `v1.4.16`
**Certified SHA:** `434a0c4a4501af08a393faaf58092add764df2a2`
**Current main head:** mutable — resolve directly from Git metadata; the latest application-code merge is PR #955 at `b403c0dcdea579e017738a6fdea138c2b1a2999c`; subsequent commits are documentation reconciliation only and are **NOT release-certified**.
**Production Certification:** v1.4.16 exact-SHA Run `37188879277` / Job `111396657270` — PASS
**W10 Internal Company Dogfood:** Run `37189332690` / Job `111398049109` — PASS
**Current status:** v1.4.17 exact-SHA candidate CERTIFIED / publication and external gates OPEN

## Immediate release-candidate priorities

1. **DONE:** W16 exact-SHA Production Certification and immutable v1.4.16 release.
2. **DONE:** W10 Internal Company Dogfood on the certified SHA.
3. **DONE:** Reconcile current documentation with the published v1.4.16 release and current `main` head.
4. **DONE:** Rebase and merge PR #836 after fresh exact-head validation.
5. **BLOCKED:** Establish GitHub `main` branch protection and required checks; the available GitHub integration lacks the required repository-rules write capability and the direct protection endpoint returned HTTP 403.
6. **DONE:** PR #927 payout-destination race hardening was merged after exact-head validation.
7. **DONE:** Reconcile W17–W23 and W10 evidence against the roadmap; W9 is already real-stack VERIFIED and is not a new implementation target.
8. **DONE:** PR #936 high-risk IntegrityError recovery audit; merged at `c59c6981ebe31ba5c99320543bac5fc14e4c7046` with all required pre-merge and post-merge engineering workflows PASS.
9. **DONE:** Repository engineering audit is now closed for the proven high-risk IntegrityError slice; no new hardening finding was confirmed through identity/provenance and retry/resume/recovery audits. **NEXT:** evidence reconciliation and release-candidate preparation; do not expand feature scope without a concrete requirement, regression, unsupported surface, or external-validation finding.


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

Canonical historical audit: `docs/current/PRODUCT_COMPLETENESS_GATE_2026-09-21.md`. Its original findings are retained as historical evidence; this file is the current priority source.

### P0 — Post-release governance cleanup

`v1.4.16` is published and exact-SHA certified at `434a0c4a4501af08a393faaf58092add764df2a2`.

1. **DONE:** exact-SHA Production Certification — Run `37188879277`, Job `111396657270`.
2. **DONE:** Product Gate failures = 0.
3. **DONE:** immutable evidence artifact emitted and uploaded.
4. **DONE:** `v1.4.16` tag and GitHub Release verified against the certified SHA.
5. **DONE:** W10 Internal Company Dogfood — Run `37189332690`, Job `111398049109`.
6. **DONE:** PR #836 was rebased onto current `main`, freshly validated at head `ea055755498bb65042e693cf011eec3eb3801b83`, and merged as `933fb68c8857f0b4fe939bb03351a726f3ec890b`.
7. **BLOCKED:** GitHub `main` branch protection and required checks remain **NOT ENABLED / NOT VERIFIED** because the available integration cannot modify repository rules and the direct protection endpoint returned HTTP 403.

### P0 — Release-candidate closure

1. **DONE:** Exact-SHA certification of candidate **v1.4.17**.
2. **DONE:** Exact target/checkout identity and Product Gates = 0.
3. **DONE:** Immutable certification evidence generated and uploaded.
4. **OPEN:** Create/verify Git tag **v1.4.17** pointing exactly to **b403c0dcdea579e017738a6fdea138c2b1a2999c**.
5. **OPEN:** Publish GitHub Release **v1.4.17** only after explicit approval.
6. **OPEN:** External production deployment and customer acceptance remain separate gates.

## P1 — External production evidence

External gates remain intentionally **OPEN — PENDING EXTERNAL EXECUTION** because the project is still being executed locally. They become actionable when an approved external target exists.

1. Establish the approved real production target and capture infrastructure identity.
2. Deploy the latest approved immutable release identity only after an external target is provisioned; the current latest certified release is `v1.4.16` at exact SHA `434a0c4a4501af08a393faaf58092add764df2a2`.
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
