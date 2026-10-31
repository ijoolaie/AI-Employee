## Verified source-audit checkpoint — 2026-10-31

Repository: `ijoolaie/AI-Employee`; default branch `main`.
Verified current main HEAD at inspection: [`8053dbabfe6a0b961336b37ec890c42b2472174f`](https://github.com/ijoolaie/AI-Employee/commit/8053dbabfe6a0b961336b37ec890c42b2472174f). This is the documentation-only merge for PR #1317; PR #1315's application merge remains `90da90d14c54bafd72983eed87b7f10d91bd042b`.

### Live GitHub triage

- Open PR inventory: **1** — #1257, intentionally Draft/on hold after explicit rejection of synthetic desktop/mobile visual evidence. Do not merge or resume World visual work until higher-priority gates are met and authenticated real-runtime evidence receives human approval.
- Open issue inventory: **9** — #1258, #1044, #1061, #1288, #1305, #19, #210, #259 and #269. Each was reviewed against its current body and available comments. Existing dispositions remain: #1258 active engineering/customer-support acceptance; #1044 deferred; #1061 blocked on real customer discovery; #1288 blocked on configured non-production SMTP, named response owner and measurable SLA; #1305 blocked on approved retention/audit/schedule; #19/#210/#259/#269 are intentional external production/RBAC/release/customer-acceptance gates. None should be closed merely to reduce the open count.
- PR #1317 is closed and its commit is present at current `main`; it corrected the master handoff to distinguish PR #1315's application merge SHA from the later documentation HEAD.

### New source-backed Shopify correctness findings — Issue #1258

Inspected current-main source in `backend/app/services/shopify_service.py`, `backend/app/models/product.py`, `backend/app/schemas/product.py`, `backend/app/services/customer_channel_service.py` and `backend/app/modules/employees/order/service.py`. Findings were recorded in [Issue #1258 comment](https://github.com/ijoolaie/AI-Employee/issues/1258#issuecomment-6539722784).

1. **Pagination can silently truncate.** `_paginate(..., max_pages=50)` returns accumulated rows even when the final page still reports `hasNextPage=true`. A caller can then treat an incomplete dataset as a successful sync. In particular, `sync_orders()` may write `last_order_sync_at` after this partial result, weakening the freshness guarantee introduced by PR #1315.
2. **Product freshness is not recorded.** `sync_products()` writes `last_product_sync_count` but no successful product-sync timestamp/watermark. Order freshness does not establish inventory freshness.
3. **Unknown inventory is collapsed into zero.** Shopify mapping uses `int(variant.get("inventoryQuantity") or 0)`; missing/null quantity becomes indistinguishable from a real zero. The Product model and response schema currently require a non-null integer, so an explicit unknown state is not represented.

### Ordered next engineering increment

1. Harden `_paginate`: if the page limit is reached while `hasNextPage` remains true, raise a clear failure rather than return partial data. Add exact-limit and over-limit tests. Assert failed/partial pagination does not mark the integration freshly synced or advance any watermark.
2. Add a product-sync freshness watermark only after complete pagination and successful persistence; do not use `Product.updated_at` as provider freshness.
3. Define and test an explicit unknown/unavailable inventory representation, distinct from a verified zero, before exposing customer-facing stock claims. Preserve manually maintained inventory semantics.
4. Keep public stock/order answers fail-closed until per-resource freshness policy and verified customer-scoped read contracts are present.

### Evidence and boundaries

This checkpoint is source inspection plus GitHub triage and an issue comment. **No tests were run, no application code was changed, and no Shopify live request, customer validation, SMTP delivery, deployment or release certification is claimed.** The existing identity verification, customer-scoped order endpoint and tenant boundaries from PR #1315 must remain intact.

Latest production-certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`; current mainline is not covered by that certification.

---

## Verified checkpoint — 2026-10-30 (after PR #1315)

Repository: [ijoolaie/AI-Employee](https://github.com/ijoolaie/AI-Employee), default branch `main`.
Application merge commit for PR #1315: [`90da90d14c54bafd72983eed87b7f10d91bd042b`](https://github.com/ijoolaie/AI-Employee/commit/90da90d14c54bafd72983eed87b7f10d91bd042b).

### Public customer identity and scoped order access — merged

PR [#1315](https://github.com/ijoolaie/AI-Employee/pull/1315) is squash-merged at `90da90d14c54bafd72983eed87b7f10d91bd042b` after **25/25 exact-head CI checks passed**.

Implementation:
- Public widget contact fields are unverified. Public conversation creation no longer creates or links a CRM Customer from those fields.
- Email ownership is verified through a six-digit, tenant/conversation-bound HMAC challenge delivered by the existing transactional email outbox. Challenge expiry is 10 minutes; there are five attempts, a 60-second resend cooldown, a three-send conversation/hour cap and a five-send tenant/email/hour cap.
- A verified address links only to exactly one active Shopify-sourced Customer in the same tenant. Duplicate matches remain unlinked.
- A minimal public order endpoint requires the conversation token, verified email, revalidated Customer UUID and Shopify-owned order metadata. The response contains only order number, status, order date, total and currency.
- Public order reads fail closed unless the channel has a configured `support_policy.commerce.max_order_staleness_seconds` between 60 and 86400, the Shopify integration is active and synced, and the order-sync watermark is valid and fresh.
- Shopify `last_order_sync_at` is advanced only after the order sync loop completes successfully.
- No anonymous `run.execute` permission or general public tool execution was granted.

Tests include HMAC binding, no CRM link before verification, PostgreSQL OTP/outbox round-trip, same-tenant other-customer order exclusion, stale-sync rejection, existing WhatsApp regression coverage, browser-to-real-API acceptance, frontend build/lint/unit/browser regressions and security/CodeQL checks.

Post-merge checks on the merge SHA were still running at the time of this checkpoint. Exact-head PR CI is green; do not conflate it with post-merge validation.

### Issue #1258 — remains OPEN

The public widget browser/API admission gate and the initial customer identity/order ownership engineering increment are implemented. Remaining acceptance gates:
- Real non-production SMTP delivery evidence for email verification and staff handoff.
- Configure and validate a freshness policy per customer channel; without it public order reads intentionally remain unavailable.
- Broader tenant/privacy acceptance, including negative cross-tenant/cross-customer cases beyond the current targeted regression.
- Named human response owner, measurable SLA and escalation; live SMTP delivery is not yet proven.
- Real customer validation and feedback.

No model-quality, live customer acceptance, live SMTP delivery, production deployment or production release certification is claimed.

### Release boundary

Latest production-certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Mainline commits and green CI do not certify production deployment or live-provider behavior. No deployment or release promotion was performed.

---

## Verified checkpoint — 2026-10-30 (after PR #1313)

Repository: [ijoolaie/AI-Employee](https://github.com/ijoolaie/AI-Employee), default branch `main`.
Current main SHA: [`50cb540fd420e74e3c55dd76275527194c582017`](https://github.com/ijoolaie/AI-Employee/commit/50cb540fd420e74e3c55dd76275527194c582017).

### Post-merge validation

- PR [#1313](https://github.com/ijoolaie/AI-Employee/pull/1313) is squash-merged. The dedicated browser-to-real-API Playwright workflow passed on the exact PR head; the merged commit is `50cb540fd420e74e3c55dd76275527194c582017`.
- All **11/11 post-merge check-runs** on that merge SHA completed successfully: DAST, validate-and-package, validate, W21 real stack, architecture, SLO contract, backend, frontend, infrastructure, and both CodeQL analyses.
- The browser/API acceptance covers disposable tenant/channel provisioning through the real API, production Next.js + Chromium against the real API proxy without public-chat endpoint mocks, conversation/token creation, message submission, Run ID, transcript read-back and invalid-token rejection.
- This is automated CI evidence for the browser/API admission and persistence boundary only. It does not prove model quality, customer-specific commerce access, live staff email delivery, full customer acceptance, production deployment or release certification.

### Issue #1258 — remains OPEN

The public-chat browser/API CI gap is closed. The remaining customer support gates are not.

Source audit findings recorded in the issue:
- Public conversation identity is currently derived from user-supplied email/phone or a generated token key; the supplied contact fields are not verified identity.
- Shopify sync associates a tenant Customer UUID with imported orders in `BusinessOrder.metadata_.customer_id`, but BusinessOrder has no first-class customer FK and `find_order_for_customer` constrains lookup by tenant only, not verified customer.
- Shopify fulfillment is mapped to coarse `cancelled` / `delivered` / `processing`; no trustworthy delivery ETA is populated.
- Product `updated_at` is a local row timestamp, not provider-observed freshness. Integration sync records counts/status but no durable successful per-resource freshness watermark. Webhook registration is not proof of event application.
- Anonymous public widget Runs have neither `created_by` nor `agent_instance_id`; `get_order` / `track_order` require `run.execute`, and ToolRegistry correctly denies them. Do not relax this gate or grant anonymous broad execution permission.

Safe next implementation requires a verified customer identity contract, a customer-scoped read-only order capability, provider freshness/unknown-state semantics, and negative tests for same-tenant cross-customer access and stale/missing data. Do not claim order/ETA/stock answers are trusted until those contracts exist.

### Other current gates

- The only pre-existing application PR is [#1257](https://github.com/ijoolaie/AI-Employee/pull/1257), Draft/on hold for human visual approval based on actual desktop/mobile runtime evidence. Do not merge on CI or synthetic screenshots alone.
- Issue [#1288](https://github.com/ijoolaie/AI-Employee/issues/1288) remains blocked on authorized non-production SMTP delivery evidence, a named human response owner and a measurable SLA/escalation.
- Issue [#1305](https://github.com/ijoolaie/AI-Employee/issues/1305) remains blocked on explicit retention-duration, audit and purge-schedule approval. Logical expiry is not physical erasure.
- Issue [#1061](https://github.com/ijoolaie/AI-Employee/issues/1061) remains blocked on five decision-maker conversations and two concrete sample/trial commitments. No demand or revenue is claimed.
- Issue [#1250](https://github.com/ijoolaie/AI-Employee/issues/1250) was closed as not planned after the official GHSA-vfj7-8cjw-p6xm / CVE-2026-93687 advisory was withdrawn on 2026-10-23. No dependency override, suppression or framework migration was applied. Reassess if the advisory is reinstated or a new defect is demonstrated.
- Issues #1044 and external gates #19, #210, #259 and #269 remain open for human visual approval, production RBAC, exact-SHA release promotion, production operations/security/DR and customer acceptance.

### Release boundary

Latest production-certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Mainline merges and green CI do not certify production deployment or live-provider behavior. No deployment or new release certification was performed.

---

## Verified checkpoint — 2026-10-30 (PRs #1310 and #1311 merged)

Application baseline: `main` at `3d3f7f72c4c5e56a4d7e3f1c73cd282c41aea10f` after the two merges below. This documentation checkpoint does not change application behavior.

- PR [#1310](https://github.com/ijoolaie/AI-Employee/pull/1310) merged as `f262a1df58ba4d8c24fccc7e4573ee04c3efe4fb`. All 15/15 exact-head checks passed before merge; all 11/11 post-merge checks on the merge SHA have now completed successfully. Missing-slot preflight skips RAG retrieval, memory retrieval/embedding and automatic memory extraction; the regression test instruments the actual provider/embedding boundaries.
- PR [#1311](https://github.com/ijoolaie/AI-Employee/pull/1311) merged as `3d3f7f72c4c5e56a4d7e3f1c73cd282c41aea10f`. It was synchronized with the #1310 merge, all 4/4 exact-head checks passed, and all 5/5 post-merge checks have now completed successfully.
- Open PR inventory: only [#1257](https://github.com/ijoolaie/AI-Employee/pull/1257), intentionally Draft/on hold for human visual acceptance. Do not merge based on CI or synthetic screenshots.
- [Issue #1258](https://github.com/ijoolaie/AI-Employee/issues/1258) remains the active engineering/product acceptance tracker. Implemented slot provenance and conservative preflight are partial increments, not proof of trusted order/payment/stock/policy outcomes, durable staff delivery, browser-to-real-API acceptance, complete tenant/privacy acceptance, or live customer acceptance.
- [Issue #1288](https://github.com/ijoolaie/AI-Employee/issues/1288) remains blocked on authorized non-production SMTP delivery evidence, a named human owner and an agreed measurable SLA. Mocked SMTP/outbox tests do not prove delivery.
- [Issue #1305](https://github.com/ijoolaie/AI-Employee/issues/1305) remains blocked on explicit owner approval of retention duration, audit requirements and purge schedule. Logical expiry is not physical erasure; do not enable purge before approval.
- [Issue #1061](https://github.com/ijoolaie/AI-Employee/issues/1061) remains blocked on real prospective-customer discovery (target: five decision-maker conversations and two concrete sample/trial commitments). No customer demand or revenue is claimed.
- [Issue #1044](https://github.com/ijoolaie/AI-Employee/issues/1044) and Draft PR #1257 remain deferred pending actual-runtime desktop/mobile evidence and explicit human visual approval. [Issue #1250](https://github.com/ijoolaie/AI-Employee/issues/1250) remains upstream advisory watch; no guessed dependency override or suppression.
- External gates #19, #210, #259 and #269 remain open for target-production RBAC, exact-SHA release promotion, production operations/security/DR and customer acceptance evidence. No repository CI result closes these gates.
- Latest production-certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. The newer mainline commits are not covered by that certification. No deployment or new release certification is claimed.

The older dated checkpoints below are retained as historical records; this verified checkpoint supersedes their pending/running descriptions of PRs #1310 and #1311.

---

## Provider-boundary follow-up — 2026-10-30

- PR #1309 is closed as superseded; its backend failure exposed a test that patched the memory-extraction facade wrapper instead of the underlying provider boundary.
- Replacement PR [#1310](https://github.com/ijoolaie/AI-Employee/pull/1310) is based on current main and instruments the real memory AI gateway and embedding function, while asserting RAG/memory retrieval is skipped during missing-slot preflight. Exact-head CI is running; do not merge until all required checks pass.
- Documentation PR [#1311](https://github.com/ijoolaie/AI-Employee/pull/1311) records this correction across the current status, priorities, customer handoff and roadmap; this update also adds the master handoff checkpoint.
- Issue #1258 remains open for trusted-evidence and policy outcomes, durable handoff/outbound approval, browser-to-real-API, full tenant/privacy acceptance and real customer validation. No production deployment or new release certification is claimed.

---

# AI-Employee master handoff — 2026-10-30

## Current checkpoint — 2026-10-30 (after PR #1307)

Repository: [ijoolaie/AI-Employee](https://github.com/ijoolaie/AI-Employee), default branch `main`.
Current main SHA: [`31e869542d12aa141745667b8d44b9c1d9650c93`](https://github.com/ijoolaie/AI-Employee/commit/31e869542d12aa141745667b8d44b9c1d9650c93).

### Customer-support Run-path preflight

- PR [#1307](https://github.com/ijoolaie/AI-Employee/pull/1307) squash-merged from exact head `f202aa0208f112ed7b8c773f2530fd276a64ae2d`; all 15/15 exact-head checks passed.
- `execute_run` now calls deterministic preflight before primary response-generation gateway invocation for conservative explicit intents: delivery ETA, variant stock, bulk discount, returns/exchanges, payment issues and damaged orders, in addition to shipping fee. It asks only the first missing required slot for one unambiguous intent. Unknown or multiple intents remain on the normal guarded model path.
- Tests cover intent detection, missing-slot selection, ambiguity and Run-path behavior asserting no gateway call while required context is missing.
- Safety boundary: customer-provided order/payment references remain untrusted claims. Preflight does not synthesize order/payment state, stock, ETA, discounts, refunds or other commercial outcomes. Complete requests continue through existing policy/tool authorization.
- Issue #1258 remains open for trusted-evidence and policy outcomes, durable handoff/outbound approval, browser-to-real-API and full tenant/privacy plus live customer acceptance. The merge closes one Run-path wiring increment, not the whole acceptance issue.

### Post-merge validation

- All **11/11 check-runs** on merge SHA `31e869542d12aa141745667b8d44b9c1d9650c93` completed successfully, with zero failures or pending checks. This is automated post-merge CI evidence, not production certification.
- No local full-suite run, live customer acceptance, production deployment, or release certification is claimed.

### Ordered next actions

1. Reconcile all 11 post-merge checks on `31e869542d12aa141745667b8d44b9c1d9650c93`; investigate any failed job and record final results.
2. Continue Issue #1258 acceptance for trusted evidence/policy outcomes, handoff/outbound approval, browser-to-real-API and tenant/privacy isolation.
3. Keep Issue #1305 physical erasure gated on explicit retention duration, audit and schedule approval.
4. Continue Issue #1288 only with authorized non-production SMTP proof, named staff ownership and measurable response SLA.
5. Continue Issue #1061 customer discovery (five decision-maker conversations and two concrete sample/trial commitments).
6. Keep World visual redesign PR #1257 Draft/on hold pending explicit visual acceptance.

### Release boundary

Latest published certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Mainline merges and green CI do not certify production deployment, live-provider behavior, customer acceptance or revenue. No deployment or release was performed.

---

# AI-Employee master handoff — 2026-10-30

## Current checkpoint — 2026-10-30 (after PR #1303)

Repository: [ijoolaie/AI-Employee](https://github.com/ijoolaie/AI-Employee), default branch `main`.
Current main SHA: [`1cb51001d3a8922b1e48c9d87b376a1cb4aa7831`](https://github.com/ijoolaie/AI-Employee/commit/1cb51001d3a8922b1e48c9d87b376a1cb4aa7831).

### Customer conversation intelligence

- PR [#1303](https://github.com/ijoolaie/AI-Employee/pull/1303) is squash-merged from exact head `c38c6dda9ab835995a5e457f9079cc49dabd9e7f`; all 23 exact-head checks passed.
- Structured slots are tenant/conversation scoped and tied to an exact customer-authored source message. Values are allowlisted and conservatively extracted; expiry, conflict invalidation, configured-city constraints and fail-closed source-value verification apply. Validated prior city can be reused in shipping preflight.
- This is an engineering implementation checkpoint, not a complete support acceptance. Issue #1258 remains open for remaining ETA/variant/bulk-discount/returns/payment Run-path journeys, durable human handoff/outbound approval, browser-to-real-API and full tenant/privacy acceptance.
- Issue #1305 tracks physical erasure. Expired rows are not reused, but remain stored until source/conversation deletion. Do not implement or enable production purge before retention duration, audit requirements and operational schedule are approved.

### Post-merge verification

- Merge SHA `1cb51001d3a8922b1e48c9d87b376a1cb4aa7831`: all **17/17 post-merge check-runs completed successfully**; zero failed or pending. No local full-suite run, live customer acceptance, production deployment or release certification is implied.
- No local full-suite execution, live customer acceptance, real SMTP delivery, production deployment or release certification is claimed.

### Ordered next actions

1. Reconcile all post-merge checks on `1cb51001d3a8922b1e48c9d87b376a1cb4aa7831`; investigate any failed job and record final results.
2. Continue Issue #1258 against the remaining Run-path and end-to-end acceptance matrix; preserve source-message provenance and tenant isolation.
3. Obtain explicit owner approval for Issue #1305 retention duration, audit and schedule before designing/enabling bounded physical purge.
4. Continue Issue #1288 only with authorized non-production SMTP proof, named staff ownership and measurable response SLA.
5. Continue Issue #1061 customer discovery (five decision-maker conversations and two concrete sample/trial commitments).
6. Keep World visual redesign PR #1257 Draft/on hold until explicit visual acceptance; do not prioritize it over reliability and customer evidence.

### Release boundary

Latest published certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Mainline merges and green CI do not certify production deployment, live-provider behavior, customer acceptance or revenue. No deployment or release was performed.

---


## Current checkpoint

Repository: [ijoolaie/AI-Employee](https://github.com/ijoolaie/AI-Employee), default branch `main`.
Checkpoint main SHA: `b028f3644aaf4346c7b975726c587da7e8c141b5` (PR #1300 squash merge).

## Customer human-handoff and outbox

- PRs [#1293](https://github.com/ijoolaie/AI-Employee/pull/1293) through [#1297](https://github.com/ijoolaie/AI-Employee/pull/1297) and [#1298](https://github.com/ijoolaie/AI-Employee/pull/1298) are merged. They cover tenant-private channel configuration, tenant-configured notification destination, durable acknowledgement, outbox outcome metrics, commit-aligned metrics, and PostgreSQL retry/dead-letter persistence.
- [PR #1300](https://github.com/ijoolaie/AI-Employee/pull/1300) is squash-merged as `b028f3644aaf4346c7b975726c587da7e8c141b5`. Its test verifies that the outbox dispatcher commits a claimed `email.send` row before publishing the exact outbox ID to `send_email_task.delay`, leaving final delivery state to `email_worker`. All 11 exact-head check-runs passed.
- [Issue #1288](https://github.com/ijoolaie/AI-Employee/issues/1288) remains the operational acceptance tracker. Automated tests cover queue persistence, routing, mocked SMTP adapter invocation, retry/dead-letter and acknowledgement behavior. They do **not** establish real SMTP delivery, staff ownership/assignment, response SLA, or customer acceptance.
- No production deployment or release certification was performed.

## Customer conversation intelligence

[Issue #1258](https://github.com/ijoolaie/AI-Employee/issues/1258) remains open. Current code has deterministic slot-planning helpers for shipping, ETA, variants, bulk discounts, returns, payment issues and damaged orders. The actual `run_service.execute_run` acceptance suite currently integrates shipping-fee preflight, not all planner intents.

Important design gap: the authorized chronological transcript is passed as model context, but prior customer-provided values are not yet persisted as trusted structured slots with provenance. The current-turn shipping preflight intentionally does not infer a city from transcript text. Next implementation increment should define tenant-scoped structured slots with source message/turn, validation, expiry/reset and conflict rules, then test a two-turn journey that reuses an authorized city while rejecting stale, unrelated and cross-tenant values. Follow with Run-path tests for trusted order/payment state, stock/returns and durable human review. Do not treat model transcript recall as verified order or payment state.

## Open pull request disposition

- [PR #1299](https://github.com/ijoolaie/AI-Employee/pull/1299) contains a documentation snapshot based on an older main SHA and is behind the current main. It should be superseded by this checkpoint rather than merged as-is.
- [PR #1275](https://github.com/ijoolaie/AI-Employee/pull/1275) and [PR #1273](https://github.com/ijoolaie/AI-Employee/pull/1273) are dependency updates whose branches are substantially behind and have diverged from current main. Rebase/update safely and rerun exact-head CI before considering merge; do not force-update their heads.
- Draft [PR #1257](https://github.com/ijoolaie/AI-Employee/pull/1257) remains intentionally deferred pending explicit visual acceptance for World issue #1044.

## Ordered next actions

1. Continue Issue #1288 only where operational evidence is missing: verify configured SMTP delivery in an authorized non-production environment, define a named staff ownership/acknowledgement process, and agree a measurable response SLA. Keep these separate from CI evidence.
2. Implement the structured tenant-scoped support-slot contract for Issue #1258, including provenance and safe retention/reset semantics; add Run-path positive/negative and cross-tenant tests.
3. Reconcile or close stale documentation PR #1299 after this checkpoint is merged. Rebase dependency PRs #1273/#1275 only through a safe update and require exact-head checks.
4. Keep Issue #1061 customer discovery as a separate product gate: target five decision-maker conversations and at least two concrete sample/trial commitments before broadening integrations.
5. Keep World visual acceptance #1044 deferred until reliability and customer-evidence gates are addressed.

## Release and evidence boundary

- Latest published certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
- Mainline merges and green CI do not certify a new release, production deployment, live-provider behavior, customer acceptance, or revenue.
- No production deployment, real customer/staff email, or release operation was performed in this checkpoint.
