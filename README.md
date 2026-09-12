# AI Employee Platform

**Latest exact-SHA certified release candidate:** `v1.4.0-rc.4` — certified commit `4cadd2df003d72de43546466a47e2c66062002c6`

**Certification:** Production Certification Run `34693535048` — SUCCESS; Product Gates: 0 failures

**Architecture baseline:** `V1.5 Agentic Operating Model` — architecture/operating-model baseline, **not a separately certified release**

**Engineering phase:** Phase 14.1–14.16 tracked engineering complete; current program is **Stage 7 External Production Certification** plus Stage 8 workforce-governance engineering

**Current mainline:** `main` contains documentation reconciliation commits after the certified candidate SHA; therefore the current HEAD is **not automatically certified** and must receive fresh exact-SHA certification before final release promotion.

**Production deployment:** **NOT VERIFIED / PENDING REAL INFRASTRUCTURE**

This repository is the vendor source of truth for the AI Employee Platform. The platform is evolving toward a **Human + Agent operating model**: supported business work can be executed by a Human, a specialized Agent, or both through shared authorization, tool, approval, audit and lifecycle contracts.

## Versioning truth

The project intentionally tracks three independent axes:

- **Release:** immutable certified product snapshot. `v1.4.0-rc.4` is the latest exact-SHA certified candidate; `v1.3.8` remains the latest historically frozen production release.
- **Architecture:** platform design generation. `V1.5` is the current Agentic Operating Model baseline.
- **Engineering phase:** implementation workstream and acceptance gate.

These are not interchangeable. A higher architecture version does not imply a higher certified release, and a completed engineering phase does not automatically create a release.

Canonical versioning rules: `docs/00_START_HERE/VERSIONING_TRUTH.md`.

## Current release truth

- `v1.4.0-rc.4` at `4cadd2df003d72de43546466a47e2c66062002c6` passed Production Certification Run `34693535048`.
- Product Gates in that certification run: **0 failures**.
- The certification is bound to that exact SHA only.
- Documentation reconciliation commits after that SHA do not inherit the certification automatically.
- `v1.3.8` remains historically certified and frozen at `fd1e74b6b4c1701f7443efc202bad161ff19618c`.
- No verified external deployment of `v1.4.0-rc.4` is recorded.

## Mainline hardening truth

Recent execution/governance hardening includes:

- PR #464 — crash-safe Agent WorkItem → Run handoff.
- PR #465 — approval-resume enqueue race closed through outbox.
- PR #466 — Run creation/outbox failure boundary hardened with nested savepoint.
- PR #467 — WorkItem cancellation fenced at the DB boundary.
- PR #468 — workflow replay after side effects prevented.
- PR #470 — unsafe workflow child retries fail closed.
- PR #473 — workflow re-entry after child commit fenced.
- PR #475 — concurrent workflow event dispatch fenced.
- PR #477 — workflow terminal states made immutable.
- PR #479 — post-timeout/terminal workflow advancement fenced.
- PR #482 — durable WorkflowRun execution lease and bounded recovery.
- PR #486 — durable parallel-branch execution lease/recovery and optimistic ownership fencing.
- PR #487 — concurrent Run execution admission serialized with a database row lock.
- PR #499 — SQLAlchemy workflow child-identity FK DDL cycle warning eliminated with `use_alter=True`, preserving FK integrity and durable child-run identity semantics.

These are engineering/release hardening records. They do not by themselves establish external production certification.

## Current P0 boundary

The remaining P0 work is external rather than a missing repository feature:

1. Real production target and immutable deployed identity.
2. Real backup/restore/DR with measured RPO/RTO.
3. Production SLO/SLI and error-budget measurement.
4. Live provider validation.
5. Vendor → Reseller → Client runtime isolation/RBAC on the deployed target.
6. Authenticated deployed-target DAST where applicable.
7. Independent penetration testing/security review.
8. Production networking and secret-management lifecycle evidence.
9. HA/failure recovery, incident response and on-call rehearsal on target.
10. Ordered Vendor → Reseller → Client acceptance and final external certification (#210/#269).

Repository CI, production-like infrastructure validation, simulated providers and synthetic tests remain supporting engineering evidence only.

## Start Here

1. `docs/00_START_HERE/VERSIONING_TRUTH.md`
2. `docs/00_START_HERE/PROJECT_OVERVIEW.md`
3. `docs/00_START_HERE/CURRENT_STATUS.md`
4. `docs/00_START_HERE/CURRENT_PRIORITIES.md`
5. `docs/DOCUMENTATION_INDEX.md`
6. `docs/releases/RELEASE_TRUTH_LEDGER.md`
7. `docs/current/PRODUCTIZATION_ROADMAP.md`
8. `docs/current/PRODUCTION_EVIDENCE_INDEX.md`
9. `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md`

Do not infer current truth from historical versioned filenames. Git tags, release records, certification evidence and deployment evidence are reconciled in the release truth ledger.

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
- Architecture V1.5: **ACTIVE OPERATING-MODEL BASELINE**.
- Phase 11 Unified Execution acceptance: **COMPLETE**.
- Phase 12 Test Center: **IMPLEMENTED / OPERATIONAL HARDENING**.
- Phase 13 Agent Teams & Marketplace: **ENGINEERING COMPLETE**.
- Phase 14.1–14.16: **ENGINEERING COMPLETE WHERE TRACKED**.
- Latest exact-SHA certified candidate: **`v1.4.0-rc.4` / `4cadd2df...`**.
- Current documentation-reconciled mainline: **fresh certification required before release promotion**.
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
