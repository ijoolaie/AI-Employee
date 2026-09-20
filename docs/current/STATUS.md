# Current Project Status

**Architecture baseline:** V1.5 Agentic Operating Model  
**Certified release baseline:** `v1.4.7`  
**Certified release commit:** `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`  
**Mainline engineering head:** `132f683f0353c3b23f5d2514285ce43124db2966`
**Mainline engineering head:** `1ed65f84cfb4e626a3617dc1889f8cf7745c1850`  
**Status date:** 2026-09-20  
**Latest certified release:** `v1.4.7`  
**Certification run:** `35498984521` — PASS (exact `v1.4.7` tag)  
**Production deployment:** PENDING REAL INFRASTRUCTURE

The architecture baseline, release identity and engineering phase are independent axes. V1.5 is not a release number. The certified `v1.4.7` release is immutable and points to the exact SHA certified by the Production Certification workflow. Historical releases remain immutable and are not rewritten.

## Executive status

Phase 11 Unified Execution acceptance is **COMPLETE**. Phase 12 Test Center P12.1-P12.6 is **IMPLEMENTED / OPERATIONAL HARDENING**. Phase 13 Agent Teams & Marketplace engineering is **COMPLETE**. Phase 14 engineering is **COMPLETE WHERE TRACKED**.

The Production Certification suite passed for the exact `v1.4.7` release identity. Certification run `35498984521` checked out SHA `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`, recorded zero Product Gate failures, and produced the release evidence artifact. This is repository/GitHub-hosted production-like certification evidence; it does not claim external production deployment.

## v1.4.7 certification evidence

The certified release SHA is `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`.

- Release tag: `v1.4.7`
- Production Certification run: `35498984521` — PASS
- Certification job: `106047204166` — PASS
- Product Gate Failures: `0`
- Frontend Playwright: `6/6` PASS
- Evidence artifact: `production-certification-evidence-v1.4.7-48a6df0ea8a2fb0624e831fbdea55ee4548807f6`
- Artifact SHA256: `86c82af5326bce9d6be634df8779bf0a0f28ca16503ee34095786858780e1427`
- `production_deployment_claimed`: `false`

The release is certified, while external production deployment remains pending.

## Historical engineering hardening context

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

These changes led into the immutable `v1.4.7` release and were certified together under the exact release SHA above.

## Release and deployment status

| Item | Status | Evidence |
|---|---|---|
| `v1.4.7` tag | VERIFIED | Exact certified release tag |
| `v1.4.7` Production Certification | PASSED | Run `35498984521`; 0 Product Gate failures |
| Certified release SHA | VERIFIED | `48a6df0ea8a2fb0624e831fbdea55ee4548807f6` |
| Sharp dependency remediation | VERIFIED | `sharp` `0.35.4` in manifest and lockfile |
| Certification evidence artifact | VERIFIED | `production-certification-evidence-v1.4.7-48a6df0ea8a2fb0624e831fbdea55ee4548807f6` |
| External production deployment | PENDING | `production_deployment_claimed=false` |


## Remaining P0 external gates

| ID | Work | Status |
|---|---|---|
| 7.1 | Immutable release & release identity | **v1.4.7 CERTIFIED / FROZEN** |
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

Certification never transfers automatically across SHAs. `v1.4.7` certification is bound specifically to `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`.

## Current frontier

The engineering/release certification frontier has been crossed: `v1.4.7` is an immutable, exact-SHA-certified release. The remaining blockers are external production infrastructure and target-environment evidence: deployment, real DR/RPO/RTO, live providers, target isolation/RBAC, DAST, independent security review, network/secrets lifecycle, HA/failure drills, on-call and customer acceptance.

The controlled deployment workflow remains fail-closed and requires real production Environment inputs. No fake values should be introduced.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.
