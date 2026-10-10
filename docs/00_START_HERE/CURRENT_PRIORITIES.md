## Latest World room layout checkpoint — 2026-10-10

- Current `main` includes the merged room-access gate (#1016), scene-config API (#1018), furniture editor (#1019), and tenant-scoped employee placements (#1021).
- PR [#1016](https://github.com/ijoolaie/AI-Employee/pull/1016) merged at `c5a7dc43ca361814543ae5657a06a8469ac26c47` after exact-head CI, both CodeQL analyses, infrastructure, recovery and DAST checks passed. Room access fails closed on query errors and requires a valid future server expiry and room-instance ID; expiry is enforced at the Three.js scene boundary.
- PR [#1018](https://github.com/ijoolaie/AI-Employee/pull/1018) merged as `8c8c62e9c7b9e01f9c99d81035d6da9a557e0e2c`. The backend provides a versioned, bounded scene-config contract and tenant-scoped update endpoint; writes require matching tenant inventory, active catalogue item, active entitlement and unexpired lease.
- PR [#1019](https://github.com/ijoolaie/AI-Employee/pull/1019) merged at `cc58accefb9ec8c2c7c6d1ed579471bcc164b401` after all 14 exact-head checks passed. Main now includes the starter room furniture editor, validated saved-layout rendering and Playwright coverage. The UI supports only the starter preset and bounded built-in furniture placements.
- PR [#1021](https://github.com/ijoolaie/AI-Employee/pull/1021) merged at `40b62245d1a7fd3685546dc5ee475b8149bd1f67` after all 14 exact-head checks passed. The versioned room config now supports bounded employee placements; the API rejects inactive or cross-tenant employee IDs, and the renderer restores employees to their normal office positions when room access is denied or expires.
- Employee placement is presentation-only. It must not change work assignments, employee status, permissions, AI runs or execution state. Only active employees in the tenant's authoritative office roster may be placed; system employees remain ineligible unless explicitly exposed by that read model.
- PR [#1023](https://github.com/ijoolaie/AI-Employee/pull/1023) is open as a **Draft** and pending exact-head CI. It adds compare-and-swap room-layout saves and a 409 conflict response to prevent stale edits from overwriting newer layouts. Do not describe stale-layout conflict handling as merged until this PR passes and merges.
- Next: complete #1023 exact-head CI and review; then continue with audited legacy-inventory reconciliation, renewal/expiry UX, support workflow completion, and manual desktop/mobile QA.
- Payment boundary unchanged: provider-specific signed/authoritative verification, replay protection and amount/currency/order matching remain blocked. World Credit remains disabled until a durable append-only ledger and atomic replay-safe debit/credit exist.
- Release boundary unchanged: latest published exact-SHA certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Engineering merges and green CI do not certify a new release or enable production payments.

## Priority reconciliation — after PR #1009 (2026-10-10)

1. **Next: connect World Mode room interaction to server authorization.** PR [#1009](https://github.com/ijoolaie/AI-Employee/pull/1009) added persistent tenant-scoped room inventory and an access decision endpoint. The Three.js scene is not yet wired to it. Query `/world-commerce/room-inventory/{item_code}/access` before opening/representing a room as available; deny on missing response, expired/unreconciled lease, inactive entitlement, suspended inventory or inactive catalogue. Add Playwright coverage for active, expired, missing and API-error cases.
2. **Legacy lease reconciliation.** Existing entitlements are not automatically backfilled to inventory. Define an audited and tenant-safe reconciliation path before granting scene access to old records.
3. **Customer renewal UX and expiry communication.** Build on the existing paid-room renewal service only after scene authorization is reliable. Order creation is not payment proof or activation; preserve separate approval/activation.
4. **Provider-specific payment verification.** Still blocked pending actual fiat provider and crypto network/token policy. Require signed/authoritative verification, replay protection, amount/currency/order matching and duplicate/failure/refund tests. Keep `gateway` and `crypto` manual approval blocked until implemented.
5. **World Credit ledger.** Disabled until durable append-only accounting and atomic replay-safe debit/credit are implemented and tested.
6. **Support workflow completion** and **manual desktop/mobile QA/release certification** remain outstanding.

PR #1009 merged at `e838c2e9a99dbc01a2e777724cc7d63c5b4a0903`. All 20 reported PR-head checks and all 12 post-merge checks on exact merge SHA `e838c2e9a99dbc01a2e777724cc7d63c5b4a0903` completed successfully. Latest published certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

## Priority reconciliation — after PR #1006 (2026-10-10)

1. **Next: room entitlement → inventory/3D scene integration.** PR [#1006](https://github.com/ijoolaie/AI-Employee/pull/1006) now displays the tenant's server-backed room entitlement and expiry, but the 3D room remains visually locked/offer-only. Implement tenant-scoped server authorization and room inventory/scene lifecycle; deny access on expired, missing, legacy-unreconciled, or unavailable entitlement state. Add backend/API, real-stack, and E2E regression coverage.
2. **Customer renewal UX and expiry communication.** Build on the existing paid-room renewal service only after scene authorization is reliable. Renewal order creation is not payment proof or activation; preserve manual review/two-person activation and provider-verification guards. Define a reliable scheduler before promising expiry reminders.
3. **Provider-specific payment verification.** Still blocked on selecting the actual fiat provider and/or crypto network/token policy. Require signed webhook or authoritative status verification, replay protection, amount/currency/order matching, and duplicate/failure/refund tests before provider approval. Keep `gateway` and `crypto` manual approval blocked until implemented.
4. **World Credit ledger.** Disabled until durable append-only accounting and atomic idempotent debit/credit with replay protection are implemented and tested.
5. **Support workflow completion.** Reply threads, attachments, scoped support sessions and auditable temporary grants remain outstanding.
6. **Manual desktop/mobile QA and release certification.** Do not infer visual acceptance or a new certified release from CI.

PR #1006 merged at `ad381ed17c5f8dedd140644f975647d3ac53b925`; its pre-merge checks passed. All 9 post-merge checks on the exact merge SHA completed successfully: frontend, backend, infrastructure, DAST, both CodeQL analyses, Validate SLO contract, validate, and validate-and-package. Latest published exact-SHA certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

## Priority reconciliation — after PR #1004 (2026-10-10)

1. **Room entitlement → inventory/3D scene integration:** use server-owned active entitlement and expiry as the authority for room access; tenant-scope all inventory/scene state, fail closed on expired or unreconciled legacy leases, and add backend/API plus real-stack/E2E regression coverage.
2. **Customer renewal UX and expiry communication:** expose lease expiry and renewal eligibility to the tenant, prevent renewal UI from implying payment/activation before the existing approval and activation controls complete, and add expiry reminders only once a reliable scheduler/notification path is defined.
3. **Provider-specific payment verification:** still blocked on selecting the actual fiat provider and/or crypto network/token policy. Require signed webhook or authoritative status verification, replay protection, amount/currency/order matching, and duplicate/failure/refund tests before allowing provider approval. Keep `gateway` and `crypto` manual approval blocked until implemented.
4. **World Credit ledger:** disabled until durable append-only accounting and atomic idempotent debit/credit with replay protection are implemented and tested.
5. **Support workflow completion:** reply threads, attachments, scoped support sessions and auditable temporary grants remain outstanding.
6. **Manual desktop/mobile QA and release certification:** do not infer visual acceptance or a new certified release from CI.

PR #1004 is merged at `4e490100d31a81e93e331dfa8b3da62f23e4a883`; its 15 PR-head checks and all 10 post-merge checks passed. This is engineering evidence only. The latest published exact-SHA certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

## Priority update — 2026-10-10: fulfillment transition guard

1. **Completed:** PR #1000 merged at `aaae36a488cadd72b59ce22d00579438edd1a233`; all 11 reported checks passed on exact PR head `ac69a6240ba1aa4cc2fa09e6a03c5d38153de45c`.
2. **Completed:** regression tests protect approval-before-fulfillment and the two-person control separating payment approval from activation.
3. **Completed:** post-merge checks reviewed: PR #1000 head 11/11 success; PR #999 merge SHA `b928aca46f46d005045e48201cadb3ec8c5d1e0b` 4/4 success.
4. **Next:** implement authoritative room entitlement/lease lifecycle (grant, duration, renewal, expiry, revocation, tenant/order correlation) with durable state and tests before connecting fulfillment to the 3D scene.
5. **Still open:** provider-specific verification/webhooks and replay protection; durable wallet ledger before World Credit; room inventory and lease lifecycle; employee placement and persisted customization-to-scene integration; manual desktop/mobile World QA; support reply/thread/attachment workflows.
6. **Boundary:** green CI does not mean live payment verification, room activation, or new release certification. Latest published exact-SHA certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

## Priority update — 2026-10-10: provider approval guard

1. **Completed:** PR #998 merged at `88fe8472864f41538b7249b8d013f4f73682ed85`; all 11 pre-merge checks passed on exact PR head `cde9c78b64a977251b3c5198d56adf6fed07267e`.
2. **Verify next:** inspect all post-merge check runs on the merge SHA. Pre-merge success does not replace post-merge validation or release certification.
3. **Next implementation slice:** add provider-specific payment verification only with a real adapter/contract, signed webhook validation, replay protection, order/amount/currency matching, and duplicate/failure-event tests. Never treat a customer-submitted transaction reference as proof of payment.
4. **Hard boundary:** gateway/crypto manual approval is blocked until verification exists; manual transfer remains an audited review path. No live payment, settlement, wallet ledger, or room activation is proven. Keep World Credit disabled until durable atomic ledger/balance accounting exists.
5. **Still open:** manual desktop/mobile World QA; room entitlements, lease renewal/expiry, employee placement and customization-to-scene integration; support reply/thread/attachment workflow. Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

# Current Priorities

**Reconciled:** 2026-10-10
**Current release:** `v1.4.17`
**Certified SHA:** `b403c0dcdea579e017738a6fdea138c2b1a2999c`
**AI Employee World PR #983:** merged as `f3f7ad6c169a5e31b1773b4a280af43b49c020c7`; all 17 workflows passed on its exact PR head `a0952cc44444e5c04c4c245653e59227b3a88a82` before merge. This is post-release engineering work and is **NOT release-certified**.
**Production Certification:** v1.4.17 exact-SHA Run `37625345534` / Job `112805570856` — PASS
**W10 Internal Company Dogfood:** Run `37189332690` / Job `111398049109` — PASS
**Current status:** v1.4.17 exact-SHA certified and published / external gates OPEN

## 2026-10-10 current engineering checkpoint

- PR #983 merged the AI Employee World visual slice plus commerce, vendor diagnostics and support escalation status APIs. All 17 automated workflows passed on exact PR head `a0952cc44444e5c04c4c245653e59227b3a88a82` before merge.
- Manual cross-device visual QA, live payment provider/webhook verification, wallet/ledger, room lease/fulfillment automation, persistent 3D customization and support reply threads remain outstanding. Do not infer production readiness from merge/CI.
- The published exact-SHA certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`; PR #983 does not change that certification boundary.

## 2026-10-09 current engineering checkpoint

- Live `main` was resolved from Git metadata to `4492ad2c3d3d0f6c2b91189e37a7614fa5ca1259` after PR #980; this is an engineering head, not a release-certified SHA.
- AI Company World F8 is merged in PR #977 (`7adeacfeca998df9af78be157bb032a9ea0a8dd8`): employee presentation slots are deterministic by immutable employee ID and `departmentId` remains `null` because the tenant-scoped office contract has no authoritative department/team/location assignment.
- PR #978 reconciled the master hand-off after F8; PR #979 reconciled status/priority docs; PR #980 reconciled the productization roadmap. Do not infer organizational assignments from names, roles, work items, runs, or response order.
- Branch protection remains **OPEN** in [Issue #975](https://github.com/ijoolaie/AI-Employee/issues/975); the connected integration cannot apply repository admin settings. Owner/admin action and a test-PR verification are required.
- No new production certification is implied. `v1.4.17` remains certified only at `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

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

Historical checkpoint text below preserves the earlier v1.4.11/v1.4.16 context and should not override the current release identity at the top of this file. The current published and exact-SHA certified release is `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c` (Run `37625345534`, Job `112805570856`). External production evidence remains open because no external target has been verified.



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


## 2026-10-10 follow-up priorities — dependency PR and World QA

1. **P0 / BLOCKED — PR #984:** fix the unintended Tailwind v4 lockfile resolution while retaining the `source-map-js@1.2.2` security update. The inspected head `5287581895464c2942dc4ae4b3f21949e51322a7` has CodeQL PASS but CI, Production Infrastructure, HA Recovery and Ephemeral DAST FAIL. Do not merge until a corrected exact head passes required checks.
2. **P1 / OPEN — World manual QA:** exercise desktop and mobile viewport, keyboard and touch controls, room interaction, employee selection, customization panel, responsive layout and accessibility/console errors. Record device/browser, steps, expected/actual result and evidence. Automated CI is not a substitute for this.
3. **P1 / OPEN — commerce completeness:** implement and validate real provider verification/webhooks, wallet ledger and idempotency, lease expiry/renewal and fulfillment, durable customization-to-3D-scene integration, and remaining support reply/thread/attachment workflows only as separate reviewable slices.
4. **P2 / OPEN — release and external evidence:** do not claim production deployment or new release certification from PR merges or CI. Keep the exact certified release at `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c` until a new exact-SHA certification is performed.

The dependency PR's security update is desirable, but its current lockfile/build regression blocks merge. Keep the existing Tailwind v3 configuration coherent unless a separately scoped v4 migration updates package metadata, PostCSS configuration, Tailwind config/content scanning, and tests together.


## PR #984 correction update — 2026-10-10

- **FIX PUSHED / VALIDATION PENDING:** commit `de9dabe66a0916ab2b2d8644cd0ef27d3eed0890` restores a lockfile coherent with Tailwind v3 while updating only `source-map-js` to 1.2.2. Tailwind 3.4.19 and `postcss-selector-parser` 6.1.4 are retained.
- The prior failures were for `5287581895464c2942dc4ae4b3f21949e51322a7`; they are historical evidence, not the result for the corrected head.
- Next: inspect all five required workflow outcomes for `de9dabe66a0916ab2b2d8644cd0ef27d3eed0890`. Do not merge until CI, CodeQL, infrastructure, HA recovery and DAST pass on this exact SHA.


## PR #984 latest correction — 2026-10-10

- **CORRECTION PUSHED / VALIDATION PENDING:** CI showed that the earlier lockfile-only correction was insufficient because the Dependabot branch also changed `frontend/package.json` to Tailwind v4. Commit `072e0c077ad18b7cb2afea1c50b8b68aa99be857` restores the manifest to `tailwindcss: ^3.4.16` so it matches the corrected lockfile and existing v3 PostCSS/config setup.
- Current lockfile retains Tailwind 3.4.19 and `postcss-selector-parser` 6.1.4 while upgrading `source-map-js` to 1.2.2.
- Re-check CI, CodeQL, infrastructure, HA recovery and DAST on exact head `072e0c077ad18b7cb2afea1c50b8b68aa99be857`. Earlier failures apply to superseded heads; do not merge until the latest required checks are green.


## Dependency PR #984 — completed 2026-10-10

- **MERGED:** `source-map-js` 1.2.2 security update; Tailwind v3 configuration retained. PR #984: https://github.com/ijoolaie/AI-Employee/pull/984
- All five required workflows passed on corrected PR head `072e0c077ad18b7cb2afea1c50b8b68aa99be857` before merge. Merge commit: `36817a54475051ac42a7a445b56a3245845dbfe8`.
- Remaining priorities are World desktop/mobile manual QA, validating payment provider/webhook behavior, ledger/idempotency, entitlement/lease integration, support workflow completion and separate release certification.


## Priority update — 2026-10-10: World commerce UI

1. **Completed:** PR #986 merged as `c0a2b063012263114bd195b68612a423610474d3`; catalogue-backed room offer supports IRR/USD/USDT selection and only displays server-configured prices.
2. **Next implementation slice:** connect the offer to the existing tenant-scoped order-create API only after verifying its request/response contract and catalogue provider/method options. Require idempotency and rely on the server to compute the amount; do not accept client prices.
3. **Hard boundaries:** do not enable World Credit until a durable wallet ledger/replay-safe balance accounting exists. Do not present gateway/crypto as verified without provider-specific adapters, webhook/signature verification, replay protection and USDT network policy.
4. **Fulfillment:** approved entitlements still need room inventory/lease duration, renewal/expiry, employee placement and persistent customization-to-scene integration.
5. **Acceptance:** manual desktop/mobile World QA and production certification remain separate open gates.


### Catalogue configuration dependency found during follow-up review

- The World commerce migration creates the catalogue table but does not seed a paid room item, and the inspected API currently exposes catalogue reads but no catalogue create/update endpoint.
- Therefore the next safe slice is **platform-admin catalogue configuration** (server-side validation of prices and allowed provider/method combinations), or an explicitly approved seed/configuration process. Do not fabricate production prices, provider names, payment methods or a USDT network.
- Only after a real catalogue entry is configured should the customer order-creation UI be connected to `POST /world-commerce/orders` with an idempotency key; server-side amount calculation remains authoritative.


### Platform-admin catalogue configuration — merged

- PR #988: https://github.com/ijoolaie/AI-Employee/pull/988
- Squash merge commit: `e8239e563aef2904fc26fe617e3e3f470819c941`.
- Exact PR head `2c7941b14940660285e8d53098abfe4aeba7f7b2`: all 16 reported checks passed.
- Platform-admin-only catalogue list/create/replace endpoints validate item codes/types, IRR/USD/USDT options, positive decimal prices, configured provider/method choices, and free-versus-paid consistency. Mutations are audited.
- Provider names/methods remain configuration labels, not proof of live payment integration.

### Customer room order creation — merged

- PR #989: https://github.com/ijoolaie/AI-Employee/pull/989
- Squash merge commit: `74224ef253a1bb3d990347e34e41dbe31827b97d`; exact PR head `8e538976163aae3bffc5ef88067a2e08987ca673` passed all 8 reported checks.
- `WorldRoomOfferPanel` now sends item code, currency, configured payment method/provider and a stable idempotency key to `POST /world-commerce/orders`. It never submits the amount.
- Backend contract review confirms server-owned pricing and per-item/currency provider-method allowlists, plus tenant-scoped idempotency conflict protection. World Credit is rejected until a wallet ledger exists.
- Order creation is not payment, payment verification or room activation.

### Next priorities

1. **P1 / OPEN — World manual QA:** desktop and mobile viewports, keyboard/touch input, room interaction, employee selection, customization panel, responsive layout, accessibility and console errors. Record browser/device, steps and evidence.
2. **P1 / OPEN — payment trust boundary:** provider-specific gateway/crypto adapters, signed webhook validation, replay protection and explicit USDT network policy. Do not treat provider labels or manually submitted references as verified payments.
3. **P1 / OPEN — durable financial/fulfillment model:** wallet ledger and replay-safe atomic balance mutations before World Credit; entitlement-backed room inventory, lease duration/renewal/expiry, employee placement and persistent customization-to-scene integration.
4. **P2 / OPEN — support and release:** support reply/thread/attachment workflows; review post-merge CI on merge SHA `74224ef253a1bb3d990347e34e41dbe31827b97d`; keep production deployment and release certification separate from PR checks. Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.


## Priority update — 2026-10-10: room offer E2E coverage

1. **Completed:** PR #992 merged at `2e8531a4495cf80ee32994d23e965c67afea6f0a`. The Playwright test covers locked-room approach, offer dialog, currency-specific catalogue pricing, and idempotent order submission with no client amount.
2. **Verify next:** wait for and inspect all post-merge checks on the merge commit; do not infer production readiness from pre-merge CI alone.
3. **Next implementation slice:** use the E2E contract as a baseline, then add provider-specific payment lifecycle tests only alongside actual adapters, signature verification, replay protection, and failure/duplicate-webhook cases.
4. **Hard boundary:** the current browser test mocks commerce APIs. No live payment, settlement, wallet ledger, or room activation is proven. Do not enable World Credit until durable atomic ledger/balance accounting exists.
5. **Manual acceptance remains open:** desktop and mobile movement/interactions, accessibility, responsiveness, and actual scene integration of room/employee entitlements.


## Priority update — 2026-10-10: order idempotency service tests

1. **Completed:** PR #994 merged at `682ee6d13173673ec4ad06dea36b6d7a6750f7a7` after all 11 pre-merge checks passed on exact head `18a3b395da634e32a4d68bb3d79ee6dfd9378a27`.
2. **Verify next:** inspect post-merge checks on the merge commit; do not infer release certification from the merge or pre-merge CI.
3. **Next implementation slice:** add provider lifecycle tests only with real provider adapters, signed webhook validation, replay protection, and duplicate/failure cases.
4. **Hard boundary:** current tests cover server pricing and idempotent order service behavior, not live payment, settlement, wallet ledger, or room activation. Do not enable World Credit until durable atomic ledger/balance accounting exists.
5. **Still open:** manual desktop/mobile World QA; room entitlements, lease renewal/expiry, employee placement and customization-to-scene integration; support reply/thread/attachment workflow; production release certification remains separate.


## World commerce payment-claim boundary — 2026-10-10 (PR #996)

- PR [#996](https://github.com/ijoolaie/AI-Employee/pull/996) merged at `f92cadcc593fea3caa464c8dd9012e78390c20e8` after all 11 reported checks passed on exact PR head `9617afab06a936cdfc47575d86e306a714305e11`.
- Added service-level tests proving that a buyer-submitted provider reference is an unverified claim: it moves the order only to `payment_submitted`, records the event, and does not approve payment or activate fulfillment. A non-buyer is forbidden from submitting a reference for the order.
- This is trust-boundary test coverage only. No live provider adapter, signed webhook, settlement proof, wallet ledger, or room activation is added or verified.
- PR #994's post-merge checks were also reviewed: all 10 reported checks passed on merge SHA `682ee6d13173673ec4ad06dea36b6d7a6750f7a7`. PR #995 reconciled the preceding checkpoint.
- Next: add provider confirmation only alongside a real provider-specific contract, signature validation, replay protection, amount/currency/order matching, and failure/duplicate-event tests. Keep World Credit disabled until durable atomic ledger accounting exists.
- Still open: manual desktop/mobile World QA; lease/entitlement expiry and fulfillment; employee placement and persistent customization-to-scene integration; support reply/thread/attachment workflows.
- Release boundary unchanged: latest published exact-SHA certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`. CI and merge evidence do not certify production readiness or activate real payments.


## Priority update — 2026-10-10: fulfillment transition guard

1. **Completed:** PR #1000 merged at `aaae36a488cadd72b59ce22d00579438edd1a233`; all 11 checks passed on exact PR head `ac69a6240ba1aa4cc2fa09e6a03c5d38153de45c` before merge.
2. **Verify next:** review all post-merge checks on the merge SHA. The initial post-merge snapshot had checks still in progress; merge is not the same as post-merge verification.
3. **Next implementation priority:** entitlement-backed room fulfillment: define room inventory and lease duration, renewal/expiry semantics, persist entitlements, and enforce activation only from an approved order. Keep transitions auditable and tenant-scoped.
4. **Still open:** live provider adapters and signed/replay-safe webhook verification; amount/currency/order matching; durable atomic wallet ledger before World Credit; employee placement and customization persistence into the 3D scene; manual desktop/mobile accessibility and interaction QA; support reply/thread/attachment workflow.
5. **Hard boundary:** PR #1000 adds tests for existing state/approver guards only. It does not implement lease/entitlement fulfillment or prove live payments. Latest published exact-SHA certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.


## Priority update — 2026-10-10: room lease expiry (PR #1002)

1. **Completed on main:** PR #1002 merged as `14bff7bebdd2568e4e16e6b0ecf141111562ca26`; exact PR head `7918b75dddb370d13d6f637008186b79e8af51f1` passed 20/20 pre-merge checks.
2. **Immediate verification:** post-merge checks on the merge SHA were 2/10 success and 8 pending/in progress at last observation; inspect again before considering post-merge validation complete.
3. **Lease behavior now implemented:** paid room catalogue entries require server-configured `lease_duration_days` (1–3650 days); fulfillment snapshots `expires_at`; expired or legacy NULL-expiry room entitlements fail closed for access; expired entitlements can be reissued through a new approved order. Configure existing paid room catalogue rows before trying to fulfill them.
4. **Next implementation priority:** close the real-payment trust boundary only with a selected provider contract, server-side signature/status verification, replay protection, and amount/currency/order matching. Keep gateway/crypto approval blocked until verification exists. Keep World Credit disabled until an append-only durable ledger and atomic replay-safe debit exist.
5. **Still open:** room inventory/employee placement; customization persistence and application to the 3D scene; automated renewal/expiry messaging and self-service renewal; support reply/thread/attachment workflow; manual desktop/mobile accessibility and interaction QA.
6. **Hard boundary:** no real payment verification, settlement, wallet ledger or production deployment is established by PR #1002. Latest published exact-SHA certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
