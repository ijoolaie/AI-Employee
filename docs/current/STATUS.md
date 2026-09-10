# Current Project Status

**Architecture baseline:** V1.5 Agentic Operating Model  
**Certified release baseline:** `v1.3.8`  
**Certified release commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`  
**Mainline engineering head:** `d7c0c088b0a79e75c9ba20daf782913968e6b4ca`  
**Status date:** 2026-09-10  
**Latest certified release:** `v1.3.8`  
**Certification run:** `34052885700` — SUCCESS  
**Production deployment:** PENDING REAL INFRASTRUCTURE

The architecture baseline, release identity and engineering phase are independent axes. V1.5 is not a release number. The certified `v1.3.8` release remains immutable; `main` is ahead of that release and contains subsequent security/reliability hardening that is not certified under the `v1.3.8` identity.

## Executive status

Phase 11 Unified Execution acceptance is **COMPLETE**. Phase 12 Test Center P12.1-P12.6 is **IMPLEMENTED / OPERATIONAL HARDENING**. Phase 13 Agent Teams & Marketplace engineering is **COMPLETE**. Phase 14 engineering is **COMPLETE WHERE TRACKED**.

The production-like certification suite has passed for the exact `v1.3.8` release identity. Subsequent mainline hardening has now closed additional P1 authorization, execution-boundary, and dependency-security findings. Those changes require a new immutable release identity and fresh SHA-pinned certification before they can be represented as certified production-release evidence.

## Mainline hardening after v1.3.8

The current `main` head is `d7c0c088b0a79e75c9ba20daf782913968e6b4ca`.

The post-`v1.3.8` hardening sequence includes:

- PR #449 — endpoint-level RBAC for Customers, Invoices, Products, Orders and Sales mutations.
- PR #450 — explicit RBAC for API-key read/create/revoke operations.
- PR #451 — `team.install` enforcement for workforce employee-template management.
- PR #452 — tenant-user RBAC for Inbox conversation reads and mutations.
- PR #453 — `billing.manage` enforcement for subscription and Stripe billing mutations.
- PR #454 — transactional tenant-Run boundary for all registered side-effect tools, closing the direct side-effect bypass.
- PR #455 — database serialization of all production Run execution, closing the pending-state idempotency race for non-Agent Runs as well as Agent Runs.
- PR #456 — release-documentation reconciliation and release-candidate downstream-gate enforcement.
- PR #457 — SHA-pinned production certification identity and exact-SHA checkout enforcement.
- PR #459 — remediation of the `sharp` 0.35.3 dependency vulnerability; frontend is now pinned to patched `sharp` 0.35.4 with a regenerated lockfile.

These changes are part of the engineering mainline but are **not certified by the `v1.3.8` certification run**. Certification evidence must be regenerated against the exact release SHA selected for promotion.

## Release and deployment status

| Item | Status | Evidence |
|---|---|---|
| `v1.3.8` tag | VERIFIED | Tag resolves to `fd1e74b...` |
| `v1.3.8` production-like certification | PASSED | Run `34052885700` |
| Mainline hardening | COMPLETE THROUGH PR #459 | Main `d7c0c088...` |
| Sharp dependency remediation | VERIFIED | `sharp` `0.35.4` in manifest and lockfile |
| New release certification for mainline | NOT YET RUN | Must bind to exact release SHA |
| Controlled production deploy | FAILED BEFORE REMOTE DEPLOYMENT | Run `34060615390` |
| Production host changed by failed run | NO EVIDENCE / NOT REACHED | SSH configuration failed first |

## Remaining P0 external gates

| ID | Work | Status |
|---|---|---|
| 7.1 | Immutable release & release identity | **v1.3.8 FROZEN; NEXT RELEASE CANDIDATE NOT YET CERTIFIED** |
| 7.2 | External production infrastructure deployment | **PENDING REAL INFRASTRUCTURE** |
| 7.3 | Real backup/restore & DR with RPO/RTO | PENDING |
| 7.4 | Production SLO/SLI & error budget | PENDING |
| 7.5 | Live provider integration validation | PENDING |
| 7.6 | Vendor → Reseller → Client runtime isolation/RBAC | PENDING external actor evidence |
| 7.7 | DAST against deployed target | PENDING |
| 7.8 | Independent penetration test/security review | PENDING |
| 7.9 | Production networking hardening | PENDING target perimeter evidence |
| 7.10 | Secret management/rotation/recovery | PENDING target lifecycle evidence |
| 7.11 | HA/failure-recovery rehearsal | PENDING target rehearsal |
| 7.12 | Incident-response drill | PENDING live operational drill |
| 7.13 | Alert ownership/on-call escalation | PENDING live paging/on-call |
| 7.14 | Final external certification & customer acceptance | PENDING |

## Evidence boundary

Repository tests, PR CI, CodeQL, local Docker, GitHub-hosted production-like validation, synthetic load/security evidence, simulated providers and local RBAC acceptance are supporting engineering/release evidence only. They do not substitute for live production deployment, live provider evidence, measured production SLO/DR, independent security/compliance review or customer acceptance.

Certification never transfers automatically across SHAs. The `v1.3.8` certification run therefore does not certify `d7c0c088b0a79e75c9ba20daf782913968e6b4ca`.

## Current frontier

Application and dependency hardening through PR #459 is complete on the current mainline. The next engineering release step is to select the production-bound mainline SHA, create an immutable release candidate from that exact SHA, and run the full SHA-pinned certification topology. After certification, the remaining blockers are external infrastructure and target-environment evidence.

The controlled deployment workflow remains fail-closed and requires real production Environment inputs. No fake values should be introduced.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.
