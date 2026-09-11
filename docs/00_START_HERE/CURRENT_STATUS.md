# Current Status

**Last reconciled:** 2026-09-11  
**Latest certified release:** `v1.3.8`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`  
**Certification run:** `34052885700` — SUCCESS  
**Current engineering mainline:** `main`  
**Current mainline SHA:** `649f8ceaedb35c4f9e61a56faaf5c58956821c1d`  
**Current release candidate:** none currently certified  
**Current status:** PRODUCTION HARDENING / SYSTEMATIC EXECUTION-BOUNDARY AUDIT

## Executive truth

The AI Employee Platform is a multi-tenant business operating platform evolving toward a **Human + Agent operating model**. Platform, Reseller and Client workspaces remain separated by tenant, role and authorization boundaries.

The certified release `v1.3.8` remains frozen at its exact certified commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`. Certification does not transfer to later mainline revisions.

Mainline has moved beyond the stale `v1.4.0-rc.1` documentation state. PRs #462 through #479 have added execution-boundary hardening, including Run serialization, WorkItem/Run crash-safety, workflow retry fences, workflow re-entry fencing, event-dispatch locking and workflow terminal-state/post-timeout fencing.

## Latest hardening sequence

Key merged hardening after the previous documentation checkpoint includes:
- PR #462 — downstream hardening following the release-candidate stabilization sequence.
- PR #464 — crash-safe Agent WorkItem → Run handoff.
- PR #465 — approval-resume enqueue race closed through the outbox path.
- PR #466 — atomic Run creation/outbox failure boundary hardened with a nested savepoint.
- PR #467 — WorkItem cancellation fenced against executable pending/waiting Agent Runs at the database boundary.
- PR #468 — workflow execution replay after side effects prevented.
- PR #470 — unsafe workflow child retries fail closed; no blind child recreation.
- PR #473 — workflow re-entry after a child commit fenced.
- PR #475 — concurrent workflow event dispatch fenced with row locking.
- PR #477 — workflow terminal states made immutable at the database boundary.
- PR #479 — workflow execution fenced after timeout/cancellation/terminal state wins between child commits.

## Current execution-boundary audit

The current mainline is hardened against several duplicate-side-effect and terminal-state races, but **stale `running` ownership remains an explicit open design boundary**.

Issue #480 tracks the next P1: design a durable execution lease/recovery mechanism for stale `WorkflowRun` and `Run` records without making `running` blindly retryable. Any recovery must transfer ownership with a durable fence so an old worker cannot continue side effects, preserve existing provider durable-call fences and child Run identity, and avoid creating a replacement execution merely because a worker disappeared.

This is intentionally separate from PR #479: PR #479 prevents continued workflow advancement after a parent timeout/cancellation/terminal transition; it does not make crashed `running` executions safely recoverable.

## Certification boundary

`v1.3.8` remains the latest certified release. The previous `v1.4.0-rc.1` Product Certification attempt (`34497132748`) is historical evidence only and is not a certification of current mainline.

The current mainline SHA `649f8ceaedb35c4f9e61a56faaf5c58956821c1d` has passed the required PR gates for PR #479, including Architecture Guard, CI, CodeQL, Runtime Isolation/RBAC, HA Failure Recovery, Production Infrastructure Validation and Ephemeral DAST, plus the additional production observability/rollback/security workflows observed on that PR head. A fresh Production Certification has **not** yet been run for this merged SHA; therefore mainline is **not certified**.

## Production deployment status

A controlled deployment was previously attempted using `v1.3.8`:
- Workflow run: `34060615390`
- Job: `101560362909`
- Result: **FAILED BEFORE REMOTE DEPLOYMENT**
- Failed step: `Configure SSH`
- Cause: required production Environment inputs were empty/missing.
- Remote deploy and deployed-identity verification were skipped.
- Production host mutation: **NONE**.

## External production gates

These remain pending and are not established by repository/production-like certification:

- real production infrastructure;
- deployed-identity verification;
- live provider validation;
- real backup/restore and DR;
- production SLO/SLI and error budget;
- external Vendor → Reseller → Client acceptance;
- DAST against the deployed target where applicable;
- independent security review;
- production networking and secret-management evidence;
- HA/failure recovery in the target environment;
- incident response/on-call evidence;
- final external certification and customer acceptance.

## Evidence boundary

CI, repository tests, CodeQL, production-like validation and simulated providers establish engineering/release evidence. They do not establish live production deployment, live provider certification, measured production SLO/DR, independent security review or customer acceptance.

Certification is bound to the exact SHA and never transfers automatically.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.
