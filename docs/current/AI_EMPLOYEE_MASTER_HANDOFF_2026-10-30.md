# AI-Employee master handoff — 2026-10-30

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
