# Current Priorities

**Reconciled:** 2026-10-04
**Current release:** `v1.4.16`
**Certified SHA:** `434a0c4a4501af08a393faaf58092add764df2a2`
**Current main head:** `933fb68c8857f0b4fe939bb03351a726f3ec890b` — post-release engineering head; **NOT release-certified**
**Production Certification:** v1.4.16 exact-SHA Run `37188879277` / Job `111396657270` — PASS
**W10 Internal Company Dogfood:** Run `37189332690` / Job `111398049109` — PASS
**Current status:** v1.4.16 RELEASE-CERTIFIED at its immutable SHA / current main is post-release engineering / EXTERNAL GATES OPEN

## Immediate post-release priorities

1. **DONE:** W16 exact-SHA Production Certification and immutable v1.4.16 release.
2. **DONE:** W10 Internal Company Dogfood on the certified SHA.
3. **DONE:** Reconcile current documentation with the published v1.4.16 release and current `main` head.
4. **DONE:** Rebase and merge PR #836 after fresh exact-head validation.
5. **BLOCKED:** Establish GitHub `main` branch protection and required checks; the available GitHub integration lacks the required repository-rules write capability and the direct protection endpoint returned HTTP 403.
6. **NEXT:** Verify current-main CI after the PR #836 merge, then select the next concrete Workforce/product hardening slice.


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

The latest code-bearing engineering head is PR #832 merge `b352ce41ab65031b5463542e254ddd3a2a1f459b`, containing the merged CI timeout process-termination fix lineage through PR #826 and governed Workforce runtime-binding fix from PR #827. PR #833 is documentation-only and merged at `3d29aeffb44bcba7d833ca906884b6dc5fca814a`. Mutable current-main SHA is intentionally resolved directly from the repository. Current-main validation remains engineering evidence only.



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
