# Current Status

**Last reconciled:** 2026-09-12  
**Latest certified release candidate:** `v1.4.0-rc.4`  
**Certified commit:** `4cadd2df003d72de43546466a47e2c66062002c6`  
**Certification run:** `34693535048` — SUCCESS  
**Certification job:** `103552962717` — SUCCESS  
**Current engineering mainline:** `main`  
**Current mainline SHA:** `4cadd2df003d72de43546466a47e2c66062002c6`  
**Current status:** RELEASE-CANDIDATE CERTIFIED / EXTERNAL PRODUCTION GATES PENDING

## Executive truth

The AI Employee Platform is a multi-tenant business operating platform evolving toward a **Human + Agent operating model**. Platform, Reseller and Client workspaces remain separated by tenant, role and authorization boundaries.

The previous certified production release `v1.3.8` remains frozen at its exact certified commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`. A later exact-SHA Production Certification has now passed for `v1.4.0-rc.4` at `4cadd2df003d72de43546466a47e2c66062002c6`. Certification is bound to the exact SHA and does not transfer to other revisions.

## Latest hardening sequence

Key merged hardening includes:
- PR #464 — crash-safe Agent WorkItem → Run handoff.
- PR #465 — approval-resume enqueue race closed through the outbox path.
- PR #466 — atomic Run creation/outbox failure boundary hardened with a nested savepoint.
- PR #467 — WorkItem cancellation fenced against executable pending/waiting Agent Runs at the database boundary.
- PR #468 — workflow execution replay after side effects prevented.
- PR #470 — unsafe workflow child retries fail closed; no blind child recreation.
- PR #473 — workflow re-entry after a child commit fenced.
- PR #475 — concurrent workflow event dispatch fenced with row locking.
- PR #477 — workflow terminal states made immutable at the database boundary.
- PR #479 — workflow advancement fenced after timeout/cancellation/terminal state wins between child commits.
- PR #482 — durable WorkflowRun execution lease, heartbeat, ownership fencing and bounded recovery.
- PR #486 — durable parallel-branch execution lease, child Run identity/step position and optimistic lease-version fencing.
- PR #487 — concurrent Celery Run execution admission serialized with a `SELECT ... FOR UPDATE` Run-row fence.
- PR #499 — SQLAlchemy workflow child-identity FK DDL cycle warning eliminated with `use_alter=True`, without weakening FK integrity or changing durable child-run identity semantics.

## Current execution-boundary audit

The concurrent `pending` Run admission race is closed by PR #487, and the workflow FK metadata cycle warning is closed by PR #499. The current certified candidate has passed the full Production Certification suite on its exact SHA.

The next engineering focus is now the external production boundary rather than inventing duplicate repository work: real deployment identity, live providers, measured production SLO/SLI, real backup/restore and DR, external actor-matrix isolation/RBAC, deployed-target DAST, independent security review, production networking/secrets, HA/failure recovery, incident response, on-call routing and ordered Vendor → Reseller → Client acceptance.

## Certification boundary

Production Certification Run `34693535048` passed for exact commit `4cadd2df003d72de43546466a47e2c66062002c6` with release identity `v1.4.0-rc.4`.

The certification evidence includes exact-SHA identity, backend/frontend validation, migrations, production-like infrastructure/readiness, OCR runtime/extraction, product gates with zero failures, and Playwright E2E. The certification is release-candidate engineering/release evidence; it is **not** external production deployment or customer acceptance.

Post-merge CI evidence also includes successful runs for SLO Contract Manual v2 (`34693267741`), Delivery Manifest Bundle (`34693267680`) and Production Compose Validation (`34693267659`) on the certified mainline SHA.

## Production deployment status

A controlled deployment was previously attempted using `v1.3.8`:
- Workflow run: `34060615390`
- Job: `101560362909`
- Result: **FAILED BEFORE REMOTE DEPLOYMENT**
- Failed step: `Configure SSH`
- Cause: required production Environment inputs were empty/missing.
- Remote deploy and deployed-identity verification were skipped.
- Production host mutation: **NONE**.

There is still no verified external deployment of `4cadd2df003d72de43546466a47e2c66062002c6` recorded in the repository evidence.

## External production gates

These remain pending and are not established by repository/production-like certification:

- real production infrastructure and deployed-identity verification;
- live provider validation;
- real backup/restore and DR with measured RPO/RTO;
- production SLO/SLI and error budget measurement;
- external Vendor → Reseller → Client runtime isolation/RBAC acceptance;
- DAST against the deployed target where applicable;
- independent penetration testing/security review;
- production networking and secret-management evidence;
- HA/failure recovery in the target environment;
- incident-response drill and alert ownership/on-call evidence;
- final external certification and customer acceptance (#210/#269).

## Evidence boundary

CI, repository tests, CodeQL, production-like validation and simulated providers establish engineering/release evidence. They do not establish live production deployment, live provider certification, measured production SLO/DR, independent security review or customer acceptance.

Certification is bound to the exact SHA and never transfers automatically.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.
