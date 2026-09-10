# Current Status

**Last reconciled:** 2026-09-10  
**Certified release:** `v1.3.8`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`  
**Certification run:** `34052885700` — SUCCESS  
**Current engineering mainline:** `main`  
**Current engineering baseline:** `decde0ad333ba972a79053b3da6489f92a2648de`  
**Status:** ENGINEERING HARDENING CONTINUES / v1.3.8 REMAINS CERTIFIED / EXTERNAL PRODUCTION PENDING

## Executive truth

The AI Employee Platform is a multi-tenant business operating platform evolving toward a **Human + Agent operating model**. Platform, Reseller and Client workspaces remain separated by tenant, role and authorization boundaries.

The certified release `v1.3.8` remains frozen at its exact certified commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`. Certification run `34052885700` passed the repository's release certification gates. Certification does not transfer to later mainline revisions.

## Current engineering mainline

After `v1.3.8`, mainline hardening continued through controlled PRs. Governance hardening closed the identified AgentInstance activation, governance-freshness, access-review, delegation-freshness and runtime-authority-fingerprint gaps. Reliability hardening subsequently closed multiple real database and provider-side-effect race windows.

Key merged governance hardening:
- PR #374 — kill-switch enforcement at WorkItem admission.
- PR #375 — PostgreSQL-serialized AgentInstance concurrency admission.
- PR #376 — direct AgentInstance activation bypass blocked.
- PR #378 — governance fingerprint freshness at activation.
- PR #379 — Access Review freshness at activation.
- PR #380 — Access Review reactivation bypass blocked.
- PR #381 — Access Review freshness enforced at execution.
- PR #382 — latest Access Review decision required at execution.
- PR #383 — delegation freshness enforced at execution.
- PR #384 — governance authority fingerprint enforced at execution.

Post-governance reliability hardening merged into mainline includes:
- PR #398 — Stripe Customer idempotency boundary.
- PR #401 — Subscription initialization race recovery.
- PR #403 — durable Stripe Customer reconciliation.
- PR #404 — Shopify webhook registration serialization.
- PR #405 — Shopify sync serialization.
- PR #406 — PaymentRefund and Shopify webhook delivery race hardening.
- PR #408 — customer upsert race hardening.
- PR #409 — Stripe Customer identity-resolution serialization.
- PR #411 — OnboardingProgress creation race recovery.
- PR #413 — transactional outbox enqueue race recovery.
- PR #415 — tenant registration and RBAC permission creation race hardening.
- PR #417 — refund lifecycle BillingEvent race recovery.
- PR #419 — BillingEvent `record_event()` race recovery.
- PR #421 — concurrent RAG indexing serialization.

The current mainline therefore contains materially stronger application-level concurrency guarantees than the `v1.3.8` certified release. These changes are engineering evidence only until promoted into a new immutable release and freshly certified.

## Current open engineering hardening

PR #423 — `hardening: enforce NULL-safe TeamInstallation scope uniqueness` — is open against current mainline. It closes a real PostgreSQL invariant gap where nullable composite UNIQUE constraints do not prevent duplicate `workspace_key IS NULL` scopes. The proposed partial unique indexes cover both default and named workspace scopes and marketplace publication provenance. It must pass the normal certification gates before merge.

## Release decision

`v1.3.8` remains the latest certified production candidate. The current mainline is a newer engineering baseline and must not be represented as certified.

A new release should be cut only after the current hardening pass and systematic execution/side-effect audit reach a deliberate release boundary. That release must receive its own exact SHA and fresh certification.

## Production deployment status

A controlled deployment was attempted using `v1.3.8`:
- Workflow run: `34060615390`
- Job: `101560362909`
- Result: **FAILED BEFORE REMOTE DEPLOYMENT**
- Failed step: `Configure SSH`
- Cause: required production Environment inputs were empty/missing.
- Remote deploy and deployed-identity verification were skipped.
- Production host mutation: **NONE**.

## Current gates

| Gate | Status | Evidence |
|---|---|---|
| Engineering implementation | HARDENING ACTIVE | Current mainline `decde0ad...` |
| Governance runtime hardening | COMPLETE | PRs #374–#384 |
| Concurrency / idempotency hardening | SUBSTANTIALLY COMPLETE | PRs #398–#421; #423 open |
| Production-like certification | PASSED | Run `34052885700` for `v1.3.8` |
| `v1.3.8` tag identity | VERIFIED | Tag → `fd1e74b...` |
| Production deployment | PENDING INFRASTRUCTURE | Run `34060615390` |
| Live provider validation | PENDING | Requires real provider credentials/endpoints |
| Real backup/restore & DR | PENDING | Requires target environment |
| Production SLO/SLI | PENDING | Requires deployed target |
| External security review | PENDING | Requires independent review |
| Customer acceptance | PENDING | Requires real customer environment/evidence |

## Roadmap position

The repository has crossed from application feature construction into **governance hardening, concurrency hardening and production-certification preparation**. Stage 7 remains the active external program stage. Stage 8 workforce governance engineering is active on mainline but is not a release identity.

The next engineering priority is to finish the current real hardening findings, then audit execution and side-effect boundaries: runtime adapters, tool execution, WorkItem/run transitions, credential use, external side effects and mutable authority surfaces.

## Evidence boundary

CI, repository tests, CodeQL, production-like validation and simulated providers establish engineering/release evidence. They do not establish live production deployment, live provider certification, measured production SLO/DR, independent security review or customer acceptance.

Certification is bound to the exact SHA and never transfers automatically.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.
