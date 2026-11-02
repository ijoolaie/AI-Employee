# AI-Employee Master Handoff — 2026-11-02

**Repository:** `ijoolaie/AI-Employee`  
**Default branch baseline:** `main` at `0c921d85fae806851fad1a58170d37bf8d46114d`  
**Architecture tracker:** [Issue #1350](https://github.com/ijoolaie/AI-Employee/issues/1350)  
**Architecture specification:** [Multi-Vendor Account, RBAC and Portal Architecture](MULTI_VENDOR_PORTAL_ARCHITECTURE_2026-11-02.md)

## 1. Latest project decision

On 2026-11-02 the user approved the multi-vendor account architecture:

- One default Vendor at launch, with multi-Vendor support built into the model from the beginning.
- Public Reseller and Customer registration attaches to the default Vendor.
- No public Vendor signup; Vendor provisioning and initial Vendor Owner creation use an authorized path.
- Vendor and Reseller child-account creation is permission-controlled and restricted to the creator's ownership boundary.
- A Reseller can manage only its own Customers and must have no read access to other Resellers or their Customers.
- Vendor, Reseller and Customer portals have separate UX and explicit portal-access grants.
- Primary identity, role, permissions, membership and active portal context are separate concepts.
- Membership activation requires verified payment or an explicitly granted Demo entitlement.

Detailed requirements and phased acceptance gates are in the architecture specification and issue #1350.

## 2. GitHub state at this checkpoint

- `main` exact HEAD: `0c921d85fae806851fad1a58170d37bf8d46114d` (PR #1336 merge).
- PR #1348: open Draft; daily Celery Beat read-only retention preview. Not merged.
- PR #1349: open Draft; GitHub Actions read-only retention preview. Not merged; requires dedicated staging database secret/variable before activation.
- PR #1257: open Draft/on hold pending authenticated real-runtime desktop/mobile evidence and human visual approval.
- Dependabot PRs #1340–#1347 are present in the open-PR inventory; review their exact-head CI and dependency context before merge.
- Issue #1350 created for the approved multi-vendor implementation.
- Issue #19 remains the separate external-production Vendor/Reseller/Customer isolation and RBAC evidence gate.
- Issue #1305 remains open for retention operational acceptance. No production cleanup is authorized or claimed.
- Latest production-certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`; current mainline commits do not inherit that certification.

## 3. Local workspace state observed

### Isolated staging worktree

Path: `C:\Users\Ali\AI-Employee\.worktrees\Ai-employee Staging`

- HEAD is detached at `0c921d85fae806851fad1a58170d37bf8d46114d`, matching `origin/main` at inspection.
- Local modifications/untracked files are staging/runtime artifacts and are intentionally preserved:
  - modified `frontend/next-env.d.ts`, `frontend/tsconfig.json`;
  - `README.local-staging.md`, `docker-compose.retention-staging.yml`, `run-retention-preview.cmd`;
  - local retention acceptance/preview/cleanup scripts;
  - Celery Beat schedule database and WAL/SHM files.
- Do not stage or commit those unrelated local runtime artifacts as part of the architecture documentation or implementation.

### Primary checkout

Path: `C:\Users\Ali\AI-Employee`

- Git status is dirty and branch `work/support-acceptance-20261017` is 153 commits behind `origin/main` at inspection.
- It contains pre-existing modified and untracked commercial portal, login, edition, test and documentation work.
- **Do not reset, clean, stash, switch, rebase, pull, fast-forward or modify the primary checkout.** Preserve all its changes.

## 4. Local staging evidence

Previously recorded local-only state (reconfirm before relying on it):

- Isolated PostgreSQL 16 and Redis containers use loopback-only ports 15434 and 16379.
- Backend API: `http://127.0.0.1:8000`; frontend Next.js development server: `http://127.0.0.1:3000`.
- Celery worker and Beat were running; retention preview is read-only and the daily task does not perform deletion.
- Synthetic two-tenant retention acceptance passed, including tenant isolation and idempotency. No real user data was purged.
- Three local test users were reported created by the user. Their credentials and roles are not recorded here and must not be inferred or changed.
- The deterministic AI provider is configured; live AI provider, external SMTP, payments and external integrations are not certified by this local stack.

Local state is not re-certified by this documentation update. Re-run checks before relying on process/container status.

## 5. Work in progress and immediate next steps

1. Reconcile the isolated worktree with the documentation branch for this handoff; preserve all staging artifacts.
2. Audit actual source code for tenant models, User/Membership, signup/login, edition dependencies, RBAC delegation, portal guards, API data scoping, commercial entitlements and existing portal UIs.
3. Publish a source-backed Gap Analysis under issue #1350. Do not duplicate Phase 14 functionality already present.
4. Add tests for ownership and authorization gaps before changing behavior.
5. Implement in small isolated PRs: ownership/provisioning, scoped authorization, signup/membership, portal context, then separate UI.
6. Update this handoff, `docs/00_START_HERE/CURRENT_STATUS.md`, the architecture tracker and the local handoff after each meaningful checkpoint, recording exact SHAs and test evidence.

## 6. Synchronization protocol

- GitHub `main` is the shared integration source of truth; never assume a local checkout is current without checking its exact SHA.
- Use a dedicated branch/worktree per implementation slice.
- Before work: inspect local Git status, branch and HEAD; inspect GitHub main, open PRs/issues and relevant CI.
- During work: keep changes scoped and preserve unrelated untracked/runtime artifacts.
- Before publishing: run focused tests, full relevant checks, `git diff --check`, and review the exact diff.
- Publish the same content/commit lineage to GitHub; verify PR head SHA and local branch SHA match.
- After merge: fetch the new main SHA into the isolated worktree, rerun required smoke checks, and update local/GitHub handoff and state.
- Never claim local/GitHub parity when one side could not be inspected or synchronized.

## 7. Safety and release boundaries

- Production database, deployment, account mutation, payment activation and destructive retention require separate explicit authorization.
- Do not alter the user's three existing local accounts without an explicit request.
- Do not treat CI as production certification, live customer acceptance or visual QA.
- Keep the original dirty primary checkout untouched.