# Current Status

**Last reconciled:** 2026-09-10  
**Latest certified release:** `v1.3.8`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`  
**Certification run:** `34052885700` — SUCCESS  
**Current engineering mainline:** `main`  
**Current mainline SHA:** `b2e2517ce0a38dc4fecd97c047328f703bdd7de6`  
**Current release candidate:** `v1.4.0-rc.1`  
**Release candidate SHA:** `b2e2517ce0a38dc4fecd97c047328f703bdd7de6`  
**Current status:** RELEASE CANDIDATE VALIDATION BLOCKED / ONE PRODUCT GATE REMAINING

## Executive truth

The AI Employee Platform is a multi-tenant business operating platform evolving toward a **Human + Agent operating model**. Platform, Reseller and Client workspaces remain separated by tenant, role and authorization boundaries.

The certified release `v1.3.8` remains frozen at its exact certified commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`. Certification does not transfer to later mainline revisions.

The current mainline is `b2e2517ce0a38dc4fecd97c047328f703bdd7de6`. It contains the post-`v1.3.8` hardening sequence through PR #461 and is being validated as `v1.4.0-rc.1`.

## Mainline hardening through PR #461

Key merged hardening includes:
- PR #449 — endpoint-level RBAC for Customers, Invoices, Products, Orders and Sales mutations.
- PR #450 — explicit RBAC for API-key read/create/revoke operations.
- PR #451 — `team.install` enforcement for workforce employee-template management.
- PR #452 — tenant-user RBAC for Inbox conversation reads and mutations.
- PR #453 — `billing.manage` enforcement for subscription and Stripe billing mutations.
- PR #454 — transactional tenant-Run boundary for registered side-effect tools.
- PR #455 — database serialization of all production Run execution to close the pending-state idempotency race.
- PR #456 — release-documentation reconciliation and release-candidate downstream-gate enforcement.
- PR #457 — SHA-pinned production certification identity and exact-SHA checkout enforcement.
- PR #459 — remediation of the `sharp` 0.35.3 dependency vulnerability.
- PR #460 — documentation/dependency synchronization after the `sharp` remediation.
- PR #461 — authentication refresh-token restoration and stabilization of Reports/Analytics and Agent WorkItem certification paths.

## Latest production certification

The latest Production Certification target is:

- Release version: `v1.4.0-rc.1`
- Exact SHA: `b2e2517ce0a38dc4fecd97c047328f703bdd7de6`
- Workflow run: `34497132748`
- Certification job: `102938351658`

The run completed with **one failed Product Gate**.

### Product Gate status

Passed:
- Auth P0
- Tenant Isolation + RBAC P0
- Conversation Tenant Isolation P0
- Employee → Run → AI → Result
- Files → Knowledge → Memory
- Admin / Developer API Keys
- Workflow → Approval → Schedule
- Orders → Sales → Invoice → Billing
- Reports / Analytics Tenant Isolation
- Unified WorkItem Human real-stack

Failed:
- **Unified WorkItem Agent real-stack**

The Agent gate reaches:

`UNIFIED AGENT WORKITEM COMMERCIAL LICENSE FIXTURE PASS`

and then fails with:

`UNIFIED AGENT WORKITEM REAL-STACK CERTIFICATION FAIL:`

with an empty assertion message. Therefore the exact failing state/assertion still requires root-cause inspection.

## Release decision

`v1.3.8` remains the latest certified release and is immutable.

`v1.4.0-rc.1` is **NOT CERTIFIED**. It is blocked by the single remaining Agent WorkItem real-stack Product Gate. No certification evidence from `v1.3.8` may be inherited by this newer SHA.

The next engineering priority is to identify and correct the actual Agent WorkItem real-stack failure, run the full required CI/security/architecture gates on the exact corrected HEAD, merge only after all required gates pass, and then rerun Production Certification against the resulting exact SHA.

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

These remain pending and are not established by the current production-like certification:

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
