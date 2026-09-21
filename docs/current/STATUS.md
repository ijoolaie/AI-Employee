# Current Project Status

**Architecture baseline:** V1.5 Agentic Operating Model  
**Certified release baseline:** `v1.4.8`  
**Latest certified release:** `v1.4.8` — exact-SHA certification PASS  
**Certified release commit:** `4f7c4676850b546a1c6bdf219ab9401202302e2d`  
**Mainline engineering head:** `b0b5c8492626901a72303ae0fe1bd99eeef6429d`  
**Status date:** 2026-09-21  
**Latest published release:** `v1.4.8`  
**Latest certified release:** `v1.4.8`  
**Certification run:** `35498984521` — PASS (exact `v1.4.7` tag)  
**Production deployment:** PENDING REAL INFRASTRUCTURE

The architecture baseline, release identity and engineering phase are independent axes. V1.5 is not a release number. The certified `v1.4.7` release is immutable and points to the exact SHA certified by the Production Certification workflow. Historical releases remain immutable and are not rewritten.

## Executive status

Phase 11 Unified Execution acceptance is **COMPLETE**. Phase 12 Test Center P12.1-P12.6 is **IMPLEMENTED / OPERATIONAL HARDENING**. Phase 13 Agent Teams & Marketplace engineering is **COMPLETE**. Phase 14 engineering is **COMPLETE WHERE TRACKED**.

The Production Certification suite passed for the exact `v1.4.7` release identity. Certification run `35498984521` checked out SHA `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`, recorded zero Product Gate failures, and produced the release evidence artifact. This is repository/GitHub-hosted production-like certification evidence; it does not claim external production deployment.

## v1.4.8 certified release

- PR #550 — WhatsApp webhook idempotency and conversation race hardening: **MERGED**.
- Merge SHA: `ea37b75d599761b91fed33e26ff13e552ae2b963`.
- PR #551 — real PostgreSQL WhatsApp concurrency coverage: **MERGED**.
- Merge SHA: `542ed5f161d306ed2a3993995562b108961dc270`.
- PR #552 — Public Chat multiple-conversation regression coverage: **MERGED**.
- Merge SHA: `84b0e9d50f25095e5a2e38d051754ed077509f4d`.
- PR #553 — Meta WhatsApp webhook replay idempotency runtime coverage: **MERGED**.
- PR #553 validated head: `2ad5aa3ceb1f5626d1a2edebd8705679ecfea440`.
- PR #553 merge SHA: `4f7c4676850b546a1c6bdf219ab9401202302e2d`.
- PR #553 head passed all six observed workflows: CI #1585, Architecture Guard #1588, CodeQL #1970, Production Infrastructure Validation #848, HA Failure Recovery Validation #591, and Ephemeral DAST Validation #804.
- The Meta replay test exercises the actual `whatsapp_meta_inbound` handler with a signed raw Meta payload and real PostgreSQL persistence, replaying the same provider message ID and verifying one message/Run admission.
- **Release status:** **PUBLISHED** — exact certified SHA `4f7c4676850b546a1c6bdf219ab9401202302e2d`.
- Completed: PostgreSQL race coverage, Public Chat regression, and Meta replay/idempotency runtime handler verification.
- Exact-SHA Production Certification: **PASS** on `4f7c4676850b546a1c6bdf219ab9401202302e2d`, run `35568392010`, job `106234691683`.
- Evidence artifact: `production-certification-evidence-v1.4.8-4f7c4676850b546a1c6bdf219ab9401202302e2d`.
- Artifact digest: `sha256:d179fe603aac3460b0e751d7ad7957fad9c3f8dedf81ed8c4a9e9e608a78aa20`.
- Certification does not transfer to current main `ee4c7c95...`.

## v1.4.7 historical certification evidence

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
| `v1.4.8` tag | VERIFIED | Exact certified release tag |
| `v1.4.8` Production Certification | PASSED | Run `35568392010`; 0 Product Gate failures |
| Certified release SHA | VERIFIED | `4f7c4676850b546a1c6bdf219ab9401202302e2d` |
| `v1.4.8` Meta replay runtime coverage | PASSED | PR #553; six supporting gates passed |
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

The v1.4.8 implementation-validation and exact-SHA certification boundaries are complete and the release is published at SHA `4f7c467...`. Current main `b0b5c849...` is 19 commits newer; the delta is documentation reconciliation plus frontend dependency updates and is not covered by v1.4.8 certification. The next release boundary is certification of the final v1.4.9 candidate SHA.

The controlled deployment workflow remains fail-closed and requires real production Environment inputs. No fake values should be introduced.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.
