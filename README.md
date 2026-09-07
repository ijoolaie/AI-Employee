# AI Employee Platform

**Release baseline:** `v1.3.8` — certified commit `fd1e74b6b4c1701f7443efc202bad161ff19618c`

**Architecture baseline:** `V1.5 Agentic Operating Model` — documentation/architecture baseline, **not a separately certified release**

**Engineering phase:** Phase 14.1–14.16 complete where tracked; current program is in Production Hardening / Stage 7 External Production Certification

**Current main:** `b117ac06047335f71583576be19c39c7bef4df01`

**Production deployment:** **NOT DEPLOYED**

**Deployment checkpoint:** Issue #343

This repository is the vendor source of truth for the AI Employee Platform. The platform is evolving from an Employee-centered implementation toward a **Human + Agent operating model**: supported business work can be executed by a Human, a specialized Agent, or both through shared authorization, tool, approval, audit and lifecycle contracts.

## Versioning truth

The project intentionally tracks three independent axes:

- **Release:** immutable product snapshot (`v1.3.8` is the current certified release candidate).
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

The certified `v1.3.8` release identity remains frozen. `main` has since received separately verified dependency hardening through PR #353.

Completed dependency-hardening PRs are #355, #356, #345, #344, #352, #346, #347, #348, #349, #354, #350, #351 and #353. Each was merged only after the required repository gates passed on the exact HEAD. The current mainline head is `b117ac06047335f71583576be19c39c7bef4df01`, and there is currently no open Dependabot dependency PR in this hardening queue.

These engineering-mainline merges do **not** create a new certified release by themselves. `v1.3.8` remains the deployment identity until an intentional production-bound change is promoted into a new release and independently certified.

## Release decision

No new production release is required at the current boundary. The remaining blockers are external infrastructure and target-environment evidence. If a future production-bound code/configuration change is intentionally selected for deployment, create a new release with its own exact SHA and certification rather than moving or mutating `v1.3.8`.

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
