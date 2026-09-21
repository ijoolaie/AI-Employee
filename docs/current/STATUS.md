# Current Project Status

**Architecture baseline:** V1.5 Agentic Operating Model  
**Certified release baseline:** `v1.4.9`  
**Latest certified release:** `v1.4.9` — exact-SHA certification PASS  
**Certified release commit:** `f1ce20c010779f5273eb5d0051da24cdd57b33f6`  
**Mainline engineering head:** `f1ce20c010779f5273eb5d0051da24cdd57b33f6`  
**Status date:** 2026-09-21  
**Latest published release:** `v1.4.9`  
**Latest certified release:** `v1.4.9`  
**Certification run:** `35575615877` — PASS (exact `v1.4.9` SHA)  
**Production deployment:** PENDING REAL INFRASTRUCTURE

The architecture baseline, release identity and engineering phase are independent axes. V1.5 is not a release number. The certified `v1.4.9` release is immutable and points to the exact SHA certified by the Production Certification workflow. Historical releases remain immutable and are not rewritten.

## Executive status

Phase 11 Unified Execution acceptance is **COMPLETE**. Phase 12 Test Center P12.1-P12.6 is **IMPLEMENTED / OPERATIONAL HARDENING**. Phase 13 Agent Teams & Marketplace engineering is **COMPLETE**. Phase 14 engineering is **COMPLETE WHERE TRACKED**.

The exact-SHA Production Certification suite passed for `v1.4.9`. Certification run `35575615877` checked out SHA `f1ce20c010779f5273eb5d0051da24cdd57b33f6`, recorded the required certification evidence, and completed successfully. This is repository/GitHub-hosted production-like certification evidence; it does not claim external production deployment.

## v1.4.9 certified and published release

- **Release status:** **PUBLISHED** — exact certified SHA `f1ce20c010779f5273eb5d0051da24cdd57b33f6`.
- Exact-SHA Production Certification: **PASS**, run `35575615877`, job `106256713583`.
- Evidence artifact: `production-certification-evidence-v1.4.9-f1ce20c010779f5273eb5d0051da24cdd57b33f6`.
- Evidence digest: `sha256:32962353a3511d7d5ae951eb6d0a44620a10211493730544342afe55f980a896`.
- `v1.4.9` GitHub Release is published, not draft, not prerelease.
- Release assets include customer, reseller, runtime, self-hosted and vendor packages plus edition manifest and SHA256SUMS.
- `v1.4.9` tag resolves to the certified SHA and `main` currently points to the same SHA.

## v1.4.8 historical certified release

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
| `v1.4.9` tag | VERIFIED | Exact certified release tag |
| `v1.4.9` GitHub Release | PUBLISHED | Not draft, not prerelease |
| `v1.4.9` Production Certification | PASSED | Run `35575615877` |
| Certified release SHA | VERIFIED | `f1ce20c010779f5273eb5d0051da24cdd57b33f6` |
| External production deployment | PENDING | Not claimed by certification |
| Customer acceptance | PENDING | No external acceptance evidence |

## Evidence boundary

Repository tests, PR CI, CodeQL, local Docker, GitHub-hosted production-like validation, synthetic load/security evidence, simulated providers and local RBAC acceptance are supporting engineering/release evidence only. They do not substitute for live production deployment, live provider evidence, measured production SLO/DR, independent security/compliance review or customer acceptance.

Certification never transfers automatically across SHAs. `v1.4.7` certification is bound specifically to `48a6df0ea8a2fb0624e831fbdea55ee4548807f6`.

## Product completeness finding — 2026-09-21

A readiness review identified product-level launch blockers that are distinct from repository certification:

- **Persian/RTL:** i18n infrastructure exists, but the customer-facing product is not fully localized; major pages still contain hard-coded English UI.
- **Employee Templates:** the backend catalog currently contains three starter templates and the UI provides list/install only. This is a foundation, not a complete commercial starter catalog.
- **Lists / tables / CRUD:** operational resource surfaces require a systematic list/detail/action parity review. Hard delete is not the default; resource lifecycle must use archive/deactivate/cancel/revoke where retention or auditability requires it.

Decision: these are genuine product requirements and must be closed before external commercial production deployment. They do not invalidate or mutate v1.4.9. Any source changes require a new candidate release and fresh exact-SHA certification.

Canonical record: docs/current/PRODUCT_COMPLETENESS_GATE_2026-09-21.md.

## Current frontier

The `v1.4.9` implementation, exact-SHA certification and publication boundaries are complete. The release tag remains pinned to `f1ce20c010779f5273eb5d0051da24cdd57b33f6`. No post-certification source changes are part of the certified snapshot.

The immediate frontier is product completeness. After the product-completeness gate passes, resume external production execution and evidence. Source changes require a new release candidate and fresh certification.

## Security rule

Do not commit production hosts, private keys, registry credentials, webhook secrets, payment secrets, customer data or environment-specific access tokens. Missing required production inputs must fail closed.


### Edition-aware Test Center gate
- Test Center acceptance is now scoped by Vendor / Reseller / Customer capability ownership.
- Shared authentication, tenant isolation/RBAC, audit, policy, safe execution and evidence controls are tested at the shared boundary.
- Edition-specific tests cover only authorized service groups; full service duplication across editions is explicitly not required.
- Cross-edition negative authorization tests remain mandatory.
