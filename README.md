# AI Employee Platform

**Certified release baseline:** `v1.3.8` — certified commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`

**Architecture baseline:** `V1.5 Agentic Operating Model` — documentation/architecture baseline, **not a separately certified release**

**Engineering phase:** Phase 14.1–14.16 complete where tracked; current program is in Production Hardening / Stage 7 External Production Certification

**Current engineering mainline:** `main` at `b2e2517ce0a38dc4fecd97c047328f703bdd7de6`

**Current release candidate under validation:** `v1.4.0-rc.1` at exact SHA `b2e2517ce0a38dc4fecd97c047328f703bdd7de6`

**Production deployment:** **NOT DEPLOYED**

**Deployment checkpoint:** Issue #343

This repository is the vendor source of truth for the AI Employee Platform. The platform is evolving from an Employee-centered implementation toward a **Human + Agent operating model**: supported business work can be executed by a Human, a specialized Agent, or both through shared authorization, tool, approval, audit and lifecycle contracts.

## Versioning truth

The project intentionally tracks three independent axes:

- **Release:** immutable certified product snapshot (`v1.3.8` is the latest certified release).
- **Architecture:** platform design generation (`V1.5` is the current Agentic Operating Model baseline).
- **Engineering phase:** implementation workstream and acceptance gate (`Phase 11` through `Phase 14`).

These are not interchangeable. A higher architecture version does not imply a higher certified release, and a completed engineering phase does not automatically create a release.

Canonical versioning rules: `docs/00_START_HERE/VERSIONING_TRUTH.md`.

## Current release truth

- `v1.3.8` remains the latest certified and frozen release identity.
- The `v1.3.8` tag resolves exactly to `fd1e74b6b4c1701f7443efc202bad161ff19618c`.
- Production certification run `34052885700` passed the complete certification suite for `v1.3.8`.
- The newer mainline candidate `v1.4.0-rc.1` is **NOT CERTIFIED**. Its latest Production Certification run is blocked by one failed Product Gate: `Unified WorkItem Agent real-stack`.
- The failing Agent gate currently emits an empty assertion message after the commercial-license fixture passes; this remains a release blocker requiring root-cause correction and fresh exact-SHA certification.
- Production deployment remains **PENDING REAL INFRASTRUCTURE**.

## Mainline hardening truth

`main` is ahead of the certified `v1.3.8` release. Current mainline is `b2e2517ce0a38dc4fecd97c047328f703bdd7de6` and contains post-release governance, reliability, RBAC, release-gate and security hardening through PR #461.

Recent hardening includes:

- PR #449 — endpoint-level RBAC for Customers, Invoices, Products, Orders and Sales mutations.
- PR #450 — explicit RBAC for API-key read/create/revoke operations.
- PR #451 — `team.install` enforcement for workforce employee-template management.
- PR #452 — tenant-user RBAC for Inbox conversation reads and mutations.
- PR #453 — `billing.manage` enforcement for subscription and Stripe billing mutations.
- PR #454 — transactional tenant-Run boundary for registered side-effect tools.
- PR #455 — database serialization of all production Run execution to close the pending-state idempotency race.
- PR #456 — release-documentation reconciliation and release-candidate downstream-gate enforcement.
- PR #457 — SHA-pinned production certification identity and exact-SHA checkout enforcement.
- PR #459 — remediation of the `sharp` 0.35.3 dependency vulnerability; frontend is now pinned to patched `sharp` 0.35.4 with a regenerated lockfile.
- PR #460 — documentation/dependency synchronization after the `sharp` remediation.
- PR #461 — restoration of authentication refresh-token handling and stabilization of Reports/Analytics and Agent WorkItem real-stack certification paths.

These changes are engineering-mainline evidence and are **not certified under the `v1.3.8` release identity**. The `v1.4.0-rc.1` candidate must receive fresh certification against its exact SHA after all remaining gates pass.

## Current certification blocker

The latest certification target is:

`b2e2517ce0a38dc4fecd97c047328f703bdd7de6`

Release version: `v1.4.0-rc.1`

All Product Gates passed except:

`Unified WorkItem Agent real-stack`

The Human WorkItem real-stack gate passes. The Agent gate reaches:

`UNIFIED AGENT WORKITEM COMMERCIAL LICENSE FIXTURE PASS`

then fails with an empty assertion message. This is the immediate P0 release blocker. The next action is to trace the full Agent WorkItem execution path rather than treating the failure as a generic retry:

`Agent WorkItem → assignment → AgentExecutionAdapter → Run creation → queue dispatch → Run execution → governance/license checks → terminal state → certification assertion`

## Release decision

`v1.3.8` remains immutable and historically certified. `v1.4.0-rc.1` is a release candidate under validation, **not certified**. Do not move the `v1.3.8` tag or inherit its certification evidence across SHAs.

## Start Here

1. `docs/00_START_HERE/VERSIONING_TRUTH.md`
2. `docs/00_START_HERE/PROJECT_OVERVIEW.md`
3. `docs/00_START_HERE/CURRENT_STATUS.md`
4. `docs/00_START_HERE/CURRENT_PRIORITIES.md`
5. `docs/DOCUMENTATION_INDEX.md`
6. `docs/releases/RELEASE_TRUTH_LEDGER.md`
7. `docs/current/PRODUCTIZATION_ROADMAP.md`
8. `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md`

Do not infer current truth from historical versioned filenames. Git tags, release records, certification evidence and deployment evidence are reconciled in `docs/releases/RELEASE_TRUTH_LEDGER.md`.

## Three workspaces

```text
Platform
   |
   +--> Reseller
   |      |
   |      +--> Client
   |
   +--> Internal Platform Operations
```

Each workspace has role-specific UX and tools. No downstream workspace receives implicit control-plane access to the workspace above it.

## Human + Agent execution

```text
WorkItem
   |
   +--> Human
   |
   +--> Agent
   |
   +--> Human + Agent
   |
   +--> Auto
```

Agents are specialized workers, not merely renamed Employees. Existing Employee entities remain compatibility structures while execution migrates toward `AgentDefinition`, `AgentInstance` and `WorkItem` abstractions.

## Test Center

Platform, Reseller and Client expose a first-class Test Center from the main dashboard. It provides role-aware health, security, Agent, tool, workflow, handoff, approval, RAG, memory, integration, webhook, usage, billing/sandbox, worker, model and E2E tests with safe-mode controls and persisted evidence.

## V1.5 engineering sequence

V1.5 is the **architecture/operating-model baseline**. The engineering phases below are delivery phases under that architecture; they are not release numbers.

```text
Phase 8  Unified Execution Foundation
   ↓
Phase 9  Platform Command Center
   ↓
Phase 10 Reseller Operations
   ↓
Phase 11 Client Business Workspace
   ↓
Phase 12 Test Center & Evidence
   ↓
Phase 13 Agent Teams / Marketplace
   ↓
Phase 14 Scale / Governance / Production
```

## Current position

- Architecture V1.4: **FROZEN FOUNDATION**.
- Architecture V1.5: **ACTIVE DOCUMENTATION / OPERATING-MODEL BASELINE**.
- Phase 11 Unified Execution acceptance: **COMPLETE**.
- Phase 12 Test Center P12.1-P12.6: **IMPLEMENTED / OPERATIONAL HARDENING**.
- Phase 13 Agent Teams & Marketplace: **ENGINEERING COMPLETE**.
- Phase 14.1–14.16: **ENGINEERING COMPLETE WHERE TRACKED**.
- Current program stage: **Production Hardening / Stage 7 External Production Certification & Customer Acceptance**.
- Production certification candidate `v1.3.8`: **CERTIFIED**.
- `v1.4.0-rc.1` at `b2e2517...`: **CERTIFICATION BLOCKED — 1 PRODUCT GATE FAILED**.
- External production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance / live provider validation: **PENDING**.

## Temporary local execution

The project can be run on a developer workstation while a production server is unavailable. Local execution is appropriate for development, debugging, UI work, integration work and non-production validation.

Local execution is not production certification. It must not be used to claim live provider validation, production SLO/SLI, real RPO/RTO, external security acceptance or customer acceptance. Use local/test credentials and providers only; never copy production secrets into source control or local artifacts.

## Release rules

- Keep `main` as vendor source of truth.
- Never mutate a published release for one reseller/client.
- Keep secrets and tenant data outside source/artifacts.
- Preserve tenant isolation and RBAC for both humans and agents.
- Every privileged action is auditable.
- CI/repository evidence is not production evidence.
- Maintain one authoritative Alembic graph.
- Reconcile every release tag to its underlying commit.
- Never inherit certification or acceptance evidence across different SHAs.

## Production deployment boundary

The repository contains a controlled `Live Production Deploy` workflow. It requires `release_ref`, explicit `DEPLOY` confirmation and a configured `production` Environment. The workflow requires real SSH/host/environment inputs and fails closed when they are absent. Do not fabricate production credentials or infrastructure evidence.

## License

The repository includes an Apache-2.0 `LICENSE` file. See `LICENSE` for the governing terms.
