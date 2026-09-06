# AI Employee Platform

**Current implementation baseline:** `V1.5 ACTIVE EXECUTION BASELINE`

**Latest published release candidate:** `v1.3.8`

**Certified release candidate:** `v1.3.8` → `fd1e74b6b4c1701f7443efc202bad161ff19618c`

**Production deployment:** **NOT DEPLOYED**

**Deployment checkpoint:** Issue #343

This repository is the vendor source of truth for the AI Employee Platform. The platform is **Agent-first, not Employee-first**: every supported business capability in Platform, Reseller and Client is designed to be executable by a Human, a specialized Agent, or both through the same WorkItem, authorization, tool, approval and audit contracts.

## Current release truth

- `v1.3.8` is a published GitHub prerelease / production candidate.
- The `v1.3.8` tag resolves exactly to `fd1e74b6b4c1701f7443efc202bad161ff19618c`.
- Production certification run `34052885700` passed the complete certification suite, including backend, frontend, migrations, OCR, product gates and critical Playwright E2E.
- A controlled production deployment was attempted with `v1.3.8` in run `34060615390` but stopped during SSH configuration because the required production Environment secrets were empty/missing.
- No production host was changed by that failed run.
- Production deployment therefore remains **PENDING INFRASTRUCTURE**.

## Start Here

1. `docs/00_START_HERE/PROJECT_OVERVIEW.md`
2. `docs/00_START_HERE/CURRENT_STATUS.md`
3. `docs/00_START_HERE/CURRENT_PRIORITIES.md`
4. `docs/DOCUMENTATION_INDEX.md`
5. `docs/releases/RELEASE_TRUTH_LEDGER.md`
6. `docs/current/PRODUCTIZATION_ROADMAP.md`

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

Agents are specialized workers, not merely renamed Employees. Existing Employee entities remain compatibility structures while execution migrates to `AgentDefinition`, `AgentInstance` and `WorkItem`.

## Test Center

Platform, Reseller and Client expose a first-class Test Center from the main dashboard. It provides role-aware health, security, Agent, tool, workflow, handoff, approval, RAG, memory, integration, webhook, usage, billing/sandbox, worker, model and E2E tests with safe-mode controls and persisted evidence.

## V1.5 execution sequence

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

- Phase 11 Unified Execution acceptance: **COMPLETE**.
- Phase 12 Test Center P12.1-P12.6: **IMPLEMENTED / OPERATIONAL HARDENING**.
- Phase 13 Agent Teams & Marketplace: **ENGINEERING COMPLETE**.
- Phase 14 engineering: **COMPLETE**.
- Production certification candidate `v1.3.8`: **CERTIFIED**.
- External production deployment: **PENDING REAL INFRASTRUCTURE**.
- Customer acceptance / live provider validation: **PENDING**.

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
