# AI-Employee master handoff — 2026-10-29

## Current checkpoint

Repository: [ijoolaie/AI-Employee](https://github.com/ijoolaie/AI-Employee), default branch `main`.
Main SHA at checkpoint start: `50854f64b700d9a85b035d64632c1885afa2b46b` (PR #1297 merge).

### What changed since the previous handoff

Customer human-handoff is now being hardened into an operationally actionable flow, not just a persisted conversation state:

- [PR #1293](https://github.com/ijoolaie/AI-Employee/pull/1293) merged as `663e56e2c57be60880dfba0eee0c49912e3bab35`: public channel responses no longer expose tenant-private channel configuration such as webhook secrets.
- [PR #1294](https://github.com/ijoolaie/AI-Employee/pull/1294) merged as `6ec014d1eac1ba3a23b8cfb5a357443132c5c1bc`: tenant administrators can configure a private handoff-notification email; the address is stored in tenant settings, changes are audited without logging the address, and there is no invented global-recipient fallback. Handoff email is queued only when a tenant destination and SMTP transport are configured.
- [PR #1295](https://github.com/ijoolaie/AI-Employee/pull/1295) merged as `1f8dbc735ea0cfac52bbe58022c2363e971a56ed`: durable tenant-scoped acknowledgement fields and endpoint; assignment/acknowledgement semantics are guarded and idempotent.
- [PR #1296](https://github.com/ijoolaie/AI-Employee/pull/1296) merged as `7bfd9ce440a39f94537b7360498f345e41772443`: low-cardinality email-outbox outcome metrics and structured logs that avoid recipient addresses, message bodies, and tenant IDs.
- [PR #1297](https://github.com/ijoolaie/AI-Employee/pull/1297) merged as `50854f64b700d9a85b035d64632c1885afa2b46b`: email outcome metrics are emitted only after the final database commit succeeds, avoiding a false success metric if durable status persistence fails.
- [PR #1286](https://github.com/ijoolaie/AI-Employee/pull/1286) and [PR #1287](https://github.com/ijoolaie/AI-Employee/pull/1287) are merged: PostgreSQL-backed transcript isolation and proof that customer follow-up messages after handoff do not create new AI Runs.
- [Issue #1288](https://github.com/ijoolaie/AI-Employee/issues/1288) remains the acceptance tracker for durable staff notification and acknowledgement. Synthetic tests and queued outbox rows are not proof of real SMTP delivery, human assignment, an SLA, or customer acceptance.

### PR #1298 — merged after exact-head validation

[PR #1298 — test: cover handoff outbox retry and dead-letter persistence](https://github.com/ijoolaie/AI-Employee/pull/1298) was squash-merged after review of the final diff and successful exact-head GitHub Actions checks.

- Merge commit: [`7ef52533e92c8af5cbc1bc4215587f2003ccda9e`](https://github.com/ijoolaie/AI-Employee/commit/7ef52533e92c8af5cbc1bc4215587f2003ccda9e).
- Adds a PostgreSQL-backed test for retry persistence (`pending`, retry timestamp and error) and exhausted retry transition (`dead`, `dead_at`).
- Corrected the test in commit [`cd8f080f978bd91bdac33a79d4f17940663381af`](https://github.com/ijoolaie/AI-Employee/commit/cd8f080f978bd91bdac33a79d4f17940663381af) to create and flush a synthetic tenant before inserting the outbox row.
- CI, CodeQL, Architecture Guard, Workforce Semantic Real-Stack E2E, W21 AI Business Network E2E, HA Failure Recovery, Production Infrastructure Validation and Ephemeral DAST all completed successfully on the tested head.
- Test guard accepts only the dedicated local `support_test` PostgreSQL database and does not send real SMTP messages.

### Ordered next actions

1. Reconcile [Issue #1288](https://github.com/ijoolaie/AI-Employee/issues/1288) against merged code and tests: configured recipient path, transactional outbox persistence, tenant isolation/deduplication, worker/adapter invocation, retry/dead-letter observability, acknowledgement/assignment semantics, and the no-new-AI-Run invariant. Keep live delivery and SLA claims explicitly unverified until separately demonstrated.
2. Reconcile [Issue #1288](https://github.com/ijoolaie/AI-Employee/issues/1288) against merged code and tests: configured recipient path, transactional outbox persistence, tenant isolation/deduplication, worker/adapter invocation, retry/dead-letter observability, acknowledgement/assignment semantics, and the no-new-AI-Run invariant. Keep live delivery and SLA claims explicitly unverified until separately demonstrated.
3. Continue [Issue #1061](https://github.com/ijoolaie/AI-Employee/issues/1061): validate one narrow customer problem with real prospective customers. Target five decision-maker conversations and at least two concrete sample/trial commitments before broadening integrations. Synthetic journeys and CI are not customer evidence.
4. Keep World visual acceptance [Issue #1044](https://github.com/ijoolaie/AI-Employee/issues/1044) deferred. Do not merge draft PR #1257 or start a new visual redesign before higher-priority reliability and customer-evidence blockers are addressed.
5. Preserve local-first boundaries. Do not perform production deployment, real customer/staff SMTP delivery, or release certification as part of this checkpoint.

### Release and evidence boundary

- Latest published certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
- `main` engineering changes and passing CI do not certify a new release, production deployment, live email delivery, customer acceptance, or revenue.
- No release or deployment was performed by this handoff update.
- The previous capability rubric remains historical until its explicit phase-level exit criteria are re-evaluated; do not inflate progress based on PR count.
