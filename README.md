# AI Employee Platform

**Certified release baseline:** `v1.3.8` — certified commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`

**Architecture baseline:** `V1.5 Agentic Operating Model` — documentation/architecture baseline, **not a separately certified release**

**Engineering phase:** Phase 14.1–14.16 complete where tracked; current program is in Production Hardening / Stage 7 External Production Certification

**Current engineering mainline:** `main` at `d7c0c088b0a79e75c9ba20daf782913968e6b4ca`

**Production deployment:** **NOT DEPLOYED**

**Deployment checkpoint:** Issue #343

This repository is the vendor source of truth for the AI Employee Platform. The platform is evolving from an Employee-centered implementation toward a **Human + Agent operating model**: supported business work can be executed by a Human, a specialized Agent, or both through shared authorization, tool, approval, audit and lifecycle contracts.

## Versioning truth

The project intentionally tracks three independent axes:

- **Release:** immutable certified product snapshot (`v1.3.8` is the current certified release).
- **Architecture:** platform design generation (`V1.5` is the current Agentic Operating Model baseline).
- **Engineering phase:** implementation workstream and acceptance gate (`Phase 11` through `Phase 14`).

These are not interchangeable. A higher architecture version does not imply a higher certified release, and a completed engineering phase does not automatically create a release.

Canonical versioning rules: `docs/00_START_HERE/VERSIONING_TRUTH.md`.

## Current release truth

- `v1.3.8` is the current certified and frozen production-candidate identity.
- The `v1.3.8` tag resolves exactly to `fd1e74b6b4c1701f7443efc202bad161ff19618c`.
- Production certification run `34052885700` passed the complete certification suite, including backend, frontend, migrations, OCR, product gates and critical Playwright E2E.
- A controlled production deployment was attempted with `v1.3.8` in run `34060615390` but stopped during SSH configuration because the required production Environment secrets were empty/missing.
- No production host was changed by that failed run.
- Production deployment therefore remains **PENDING INFRASTRUCTURE**.

## Mainline hardening truth

`main` is ahead of the certified `v1.3.8` release. The current mainline head is `d7c0c088b0a79e75c9ba20daf782913968e6b4ca` and contains post-release security/reliability hardening through PR #459.

Recent hardening includes:

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

These changes are engineering evidence on `main`; they do **not** retroactively change the certified `v1.3.8` artifact. A new release identity must be selected and certified against its exact immutable SHA before promotion.

## Current certification boundary

The next release candidate must use an immutable commit SHA and a release identity, and production certification must verify that the checked-out commit exactly matches the supplied SHA. The current `production-certification.yml` workflow enforces this contract for manual certification and preserves tag-based certification for release tags.

Repository-level CI, production-like infrastructure validation, HA recovery rehearsal and ephemeral DAST are engineering gates. They are not substitutes for real target-environment deployment, live provider validation, external security review, or customer acceptance.

**Current state:** engineering mainline is hardened through PR #459; `v1.3.8` remains the latest certified release; a new immutable mainline release candidate is **not yet certified**.
