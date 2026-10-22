## Progress checkpoint — Software Developer capability binding merged (2026-10-14)

PR [#1144](https://github.com/ijoolaie/AI-Employee/pull/1144) was squash-merged as [`3a95c0649c0f884f43d694c0a9dd76c060c3d70c`](https://github.com/ijoolaie/AI-Employee/commit/3a95c0649c0f884f43d694c0a9dd76c060c3d70c), from exact tested head [`f47b25a764c7b39696ae78b55e5991d630999894`](https://github.com/ijoolaie/AI-Employee/commit/f47b25a764c7b39696ae78b55e5991d630999894). All 28 check runs passed on that exact head.

The `ai_software_developer` role now explicitly binds its approval-gated `git_commit_proposal` capability to `workforce_git_commit_proposal`. A regression test checks the exact binding, `run.execute` permission, and human-approval gate. This closes a role-contract/Tool Registry binding gap; it does **not** implement Git commit execution. The provider does not yet execute this operation, so no actual Git write or live GitHub integration is claimed.

Progress rubric unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%; full-scope context 46%. Next: continue the bounded Software Developer path audit from registry dispatch through semantic handler, provider support, and persisted execution/result evidence; identify and test the next evidenced mismatch. No deployment or broad external engineering execution is claimed.

---

## Progress checkpoint — truncated CI-status response regression merged (2026-10-14)

PR [#1143](https://github.com/ijoolaie/AI-Employee/pull/1143) was squash-merged as [`6d17a52ea4c607e371f5acc197c7f82e9ef4bba9`](https://github.com/ijoolaie/AI-Employee/commit/6d17a52ea4c607e371f5acc197c7f82e9ef4bba9), from exact tested head [`045a37c6cfb8b36f8e6d09e8d81698bd20dd48a6`](https://github.com/ijoolaie/AI-Employee/commit/045a37c6cfb8b36f8e6d09e8d81698bd20dd48a6). All 13 check runs passed on that exact head.

Added a regression test proving the read-only GitHub CI-status provider handles a truncated response body (`http.client.IncompleteRead`) as `provider_error` with `executed=False`, rather than allowing an uncaught exception. This complements the prior provider stream-error hardening.

**Evidence boundary:** the test uses a mocked response; it does not prove live GitHub connectivity, production provider configuration, or external CI execution. For branch-creation writes, an unreadable response still leaves the external outcome unverified.

Progress rubric unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%; full-scope context 46%. Next: continue the source/test-backed Software Developer role audit across role contract → Tool Registry → semantic handler → provider → persisted result and failure tests. Do not claim deployment or broad external engineering execution without separate evidence.

---

## Progress checkpoint — incomplete HTTP response stream handling merged (2026-10-14)

PR [#1142](https://github.com/ijoolaie/AI-Employee/pull/1142) was squash-merged as [`b3da7b6273e6967d6f34797fb24a5c10a2f92783`](https://github.com/ijoolaie/AI-Employee/commit/b3da7b6273e6967d6f34797fb24a5c10a2f92783), from exact tested head [`605d482d063615a7befa057e2d2916f5e4865679`](https://github.com/ijoolaie/AI-Employee/commit/605d482d063615a7befa057e2d2916f5e4865679). All 17 check runs passed on that exact head.

The GitHub engineering provider now catches `http.client.HTTPException` response-stream failures in addition to transport resets and OS-level read errors. Regression tests cover `ConnectionResetError` and truncated-body `IncompleteRead` for both branch lookup and branch creation; covered failures fail closed as `provider_error` with `executed=False`.

**Evidence boundary:** if the branch-create response body cannot be read, GitHub may already have accepted the write; its external outcome remains unverified. These mocked regression tests and passing CI do not prove live GitHub provider configuration or production execution.

Progress rubric unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%; full-scope context 46%. Next: continue the source/test-backed Software Developer role audit across role contract → registry → semantic handler → provider → persisted result and failure tests. Do not claim deployment or broad external engineering execution without separate evidence. A3/A4 remain externally gated.

---

## Progress checkpoint — provider response stream errors fixed and merged (2026-10-14)

PR [#1141](https://github.com/ijoolaie/AI-Employee/pull/1141) was squash-merged as [`d1751bea33b6fd0c0eb024cc11984dba754dab78`](https://github.com/ijoolaie/AI-Employee/commit/d1751bea33b6fd0c0eb024cc11984dba754dab78), from exact tested head [`c142997b06a19446015f57b04e31cbf3e9b7c4b2`](https://github.com/ijoolaie/AI-Employee/commit/c142997b06a19446015f57b04e31cbf3e9b7c4b2). All 17 check runs passed on that exact head, including backend, provider-contract, frontend, semantic E2E, security/privacy, CodeQL, DAST, infrastructure, architecture, observability, recovery, rollback, tenant isolation/RBAC, and real-stack checks.

The change catches generic `OSError` failures while reading GitHub provider response bodies and adds regression tests for a connection reset during branch lookup and branch-create response reads. Failures return `provider_error` with `executed=False` in the covered code path. Important evidence boundary: if the create response stream fails, GitHub may already have accepted the write; external outcome remains unverified. This does not prove live GitHub connectivity or production provider configuration.

A0/A1/A2/A3/A4 remain 100/30/100/0/0; actionable progress remains 77%, full-scope context 46%. These are rubric indicators, not production or commercial readiness. Next: continue the source/test-backed A1 role/provider audit and select the next bounded gap from inspected code and tests. A3/A4 remain externally gated.

---

## Progress checkpoint — GitHub CI-status provider failure-path tests merged (2026-10-14)

PR [#1139](https://github.com/ijoolaie/AI-Employee/pull/1139) was squash-merged as [`bdf6efbc777af41d2fb8081ff93708bc0aed8c33`](https://github.com/ijoolaie/AI-Employee/commit/bdf6efbc777af41d2fb8081ff93708bc0aed8c33) from exact tested head [`e7c3f31842f0449451633b337ce60e0623c62080`](https://github.com/ijoolaie/AI-Employee/commit/e7c3f31842f0449451633b337ce60e0623c62080). All 13 check runs passed on that exact head, including frontend, backend, provider-contract, semantic E2E, security, infrastructure, architecture, and recovery checks.

Regression tests cover read-only GitHub CI-status provider timeout, HTTP 503, and syntactically invalid JSON; each must return `provider_error` and `executed=False`. Existing coverage includes missing tenant-to-repository mapping, transport errors, and malformed response shapes/fields. This is deterministic failure-path test evidence, not proof of live GitHub connectivity, production provider configuration, or external execution.

A0/A1/A2/A3/A4 remain 100/30/100/0/0; actionable progress remains 77%, full-scope context 46%. These rubric indicators are not production or commercial readiness. Next: continue the source/test-backed A1 role/provider audit and choose the next bounded gap from inspected code and tests. A3/A4 remain externally gated.

## Progress checkpoint — website health provider merged (2026-10-14)

PR [#1135](https://github.com/ijoolaie/AI-Employee/pull/1135) was squash-merged as [dce5371656fba372b0df06f3c25a010fdbb7e747](https://github.com/ijoolaie/AI-Employee/commit/dce5371656fba372b0df06f3c25a010fdbb7e747) from exact tested head [cd8414eea9dc483aaa0a9fb75dbf21a49f5e5c54](https://github.com/ijoolaie/AI-Employee/commit/cd8414eea9dc483aaa0a9fb75dbf21a49f5e5c54). All 32 check runs on that exact head completed successfully, including CI, CodeQL, provider contract, semantic real-stack E2E, W0–W6 contract gate, W2/W3/W4/W5/W6/W7/W8/W9/W10/W21/W22/W23, DAST, HA recovery, infrastructure, architecture, observability, release identity, secret management, rollback/alerting, and documentation consistency.

The bounded implementation adds a read-only website health check using tenant/site aliases mapped to operator-configured HTTPS URLs, a bounded timeout, redirect disabling, URL validation, and tenant-scoped persisted health evidence. It does not configure or verify any live website target, and does not implement preview/build/deploy/rollback or prove production website health.

PR [#1132](https://github.com/ijoolaie/AI-Employee/pull/1132) remains verified at merge `5c62de7a399250332716dc714bd9f53d09bfce38` from exact tested head `5e0d34df85021be1ddfc24aa551e12a6aa25911d`; it proves persistence of caller-supplied SEO research context, not external search-engine execution or SEO outcomes.

A0/A1/A2/A3/A4 remain 100/30/100/0/0; actionable progress 77%, full-scope context 46%. These are rubric indicators, not commercial or production readiness. Next: continue the source/test-backed A1 role-by-role capability audit and choose the next bounded implementation only after reviewing the operation's provider, permission, tenant-isolation, and failure-path evidence.

## Current progress accounting — 2026-10-14 after PR #1129

PR #1129 merged as ece6b805f02a28b27cb30da34e31dcf2efb132f7 from tested head d593b5650673174ce9579df166f9a72b76904f9e. It repairs the W16 skill-provider real-stack test fixture by setting up valid tenant-scoped Agent Run and approval context. W16, backend/frontend CI, W21, Architecture Guard, CodeQL, Ephemeral DAST, HA recovery and Production Infrastructure Validation passed on that exact head. This is deterministic test-provider evidence only; it does not establish live external provider execution or production readiness.

A2 remains 12/12 = 100%. A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress = (100 + 30 + 100) / 3 = 76.7% (77%); full-scope context = (100 + 30 + 100 + 0 + 0) / 5 = 46%. These are rubric indicators, not commercial readiness. A1 audit increment: AI Trader, Internal Manager, Marketing Manager, QA/DevOps, Website, Content Producer, Graphic Designer and Social Media have source-backed boundaries recorded. Content QA is structural only; image generation and social execution are not configured. Continue the role audit and select bounded implementation increments with failure-path and tenant-isolation tests before changing A1. Next priority: continue A1 capability reality audit with source-backed evidence, then validate configured providers and operational/release gates before supervised pilot acceptance.

---

# AI Employee — Mandatory Working Rules for AI Agents

**Status:** Active repository-wide instructions  
**Applies to:** Every AI assistant/agent working in this repository, every session, every task, and every continuation such as “continue” / «ادامه بده».

## 1. Read before acting; re-read before each continuation

At the beginning of every task or resumed session:

1. Read this file first.
2. Read `docs/00_START_HERE/CURRENT_STATUS.md` and `docs/00_START_HERE/CURRENT_PRIORITIES.md`.
3. Read `docs/current/STATUS.md` if present, then the latest relevant master handoff and task-specific canonical/evidence documents.
4. Check the live repository state, current branch/commit, relevant issues and PRs, and available CI evidence before asserting what is current.
5. Resolve disagreements using `docs/DOCUMENTATION_GOVERNANCE.md` and its source-of-truth hierarchy. Do not treat an old handoff or memory as proof of current GitHub state.

If a required source or tool is inaccessible, say exactly what could not be inspected and continue only within that limitation. Never imply these rules were followed if the files could not be read.

## 2. Every response that reports work must show project progress

Whenever work is performed, and whenever reporting a checkpoint, include a compact **Project Progress** section with:

- **Overall goal:** the end result being pursued.
- **Current stage:** the stage worked on in this turn.
- **Stage status:** completed / in progress / blocked / deferred.
- **Evidence:** exact commit, PR, issue, test/workflow run, artifact, or file links that support the status.
- **Progress measure:** completed stages out of the explicitly defined total, or accepted criteria passed out of total. Calculate a percentage only when the denominator is real and defined. If no defensible denominator exists, say “percentage not yet measurable” rather than inventing one.
- **What changed this turn:** concrete changes and their verification status.
- **Remaining work:** outstanding acceptance criteria and blockers.

Never equate code written, a PR opened, a green CI run, a screenshot, or documentation updated with full feature completion, release certification, production deployment, customer acceptance, or revenue. State exactly which claim the evidence supports.

## 3. Always show the path before and after the current step — all the way to completion

At the start of a task, state the sequence of stages from the current position through the final intended outcome. At each checkpoint, show:

1. **Previous stage(s):** what has already been completed, with evidence; or mark as unverified.
2. **Current stage:** the exact work being done and its acceptance criteria.
3. **Next stage(s):** the remaining ordered steps, including the final completion/acceptance stage.
4. **Exit condition:** what concrete evidence will allow the current stage to be called complete.

Keep this sequence updated as facts change. Do not stop at “next steps” without identifying the remaining path to the ultimate goal. Do not mark future stages complete in advance. If a blocker changes the path, explain the change and its impact on overall progress.

## 4. Work to completion; control scope

- Prefer finishing and verifying existing priorities over inventing new features, refactors, documentation files, or speculative improvements.
- Follow the canonical priority order. Work in bounded, reviewable increments with explicit acceptance criteria.
- For a feature, trace the relevant end-to-end path (UI/API/business logic/persistence/integrations/authorization/audit as applicable), not merely the visible UI or placeholder.
- Resolve open PRs and blockers deliberately: merge, fix, close, or defer with a recorded reason. Do not leave ambiguous statuses.
- Do not broaden scope mid-task unless evidence reveals a necessary dependency, security issue, correctness defect, or user explicitly changes priority.
- “Continue” means advance the next valid stage in the established plan, not restart planning, repeat finished work, or add unrelated work.
- Do not claim to have edited files, run commands/tests, inspected screenshots, created commits, opened/merged PRs, or deployed anything unless the relevant tool actually confirms it.

## 5. Verify proportionately and report truthfully

- Inspect current branch and exact commit before changing files. Preserve user changes and local/untracked configuration; do not overwrite or discard them.
- Use isolated branches/worktrees for code changes when the available workflow supports them. Avoid direct commits to the protected/default branch for implementation work; follow repository policy.
- Run the narrowest relevant checks first, then required broader CI/security/contract/E2E checks in the repository's prescribed order.
- When visual UI changes are involved, inspect fresh desktop and mobile evidence where applicable. A static screenshot proves layout at that instant, not animation behavior over time.
- Separate pre-merge exact-head evidence from post-merge evidence, and record the SHA each result applies to.
- Distinguish PASS, FAIL, BLOCKED, NOT RUN, and NOT APPLICABLE. Never present “not run” as pass.
- Keep CI cost-free and mock-based where required. Paid APIs, billing, Shopify, and real secrets must remain Production-only unless canonical policy explicitly changes.
- Never expose secrets, credentials, personal data, or sensitive environment values in logs, commits, screenshots, or reports.

## 6. Preserve product, release, and deployment truth

- Treat the exact release tag/SHA and its certification evidence as immutable.
- Current `main` work does not inherit release certification automatically.
- Engineering tests/rehearsals do not prove external production deployment, live provider operation, customer acceptance, or realized revenue.
- Do not call AI Employee World or any role/capability “complete” while its broader acceptance criteria remain open.
- Preserve existing architectural, accessibility, tenant isolation/authorization, security, reduced-motion, desktop/mobile, and operational constraints.
- Follow existing canonical documentation governance. Update existing canonical documents rather than creating parallel status/roadmap/release-truth files.

## 7. Documentation and handoff are part of the task, not a substitute for implementation

When a meaningful task changes implementation status or verified facts:

- Update the appropriate existing canonical status/priority/handoff documents, following repository governance and the established workflow.
- Record what changed, what was tested, exact evidence links and SHAs, what remains, known limitations, blockers, and the precise next action.
- Keep plans, implementation facts, test evidence, release status, and production status separate.
- Do not create redundant documents just to report progress. Use this file for persistent agent rules; use canonical project documents for project status.

## 8. Required response format for each work checkpoint

Use this structure, adapted concisely to the task:

### Project Progress
- **Goal:** …
- **Current stage:** Stage X of N — …
- **Status:** …
- **Evidence:** …
- **Measured progress:** X/N accepted stages or criteria; percentage only if meaningful.
- **Completed this turn:** …
- **Not yet verified / blocked:** …

### Delivery path
- **Previous:** completed stages and evidence, or explicitly “not re-verified”.
- **Now:** current work and exit criteria.
- **Next:** ordered remaining stages through final acceptance/release, with the final goal named.
- **Next action:** one concrete action that advances the plan.

At final delivery, state the final acceptance criteria and their evidence, list any exceptions or deferred items, and explicitly say whether the intended goal is complete, partially complete, or blocked.

## 9. Final definition of done

A task is complete only when its stated acceptance criteria have been met and verified, required checks have run, evidence is recorded, relevant canonical documentation is reconciled, and the user is told what is still outside scope. A project or release is complete only against its separately documented end-to-end acceptance/release criteria—not because a single task or CI workflow passed.


## 10. Progress accounting: agent-actionable vs external-only work

Report two distinct progress figures whenever a project tracker contains work that may require live infrastructure or third parties:

1. **Agent-actionable progress (primary working-progress figure):** average only the explicitly defined stages/criteria that can be advanced and verified through repository inspection, code changes, static analysis, unit/contract tests, local fixtures, and available repository CI. Exclude criteria that inherently require access not available in this session, such as a customer-operated server, private production environment, live third-party provider credentials, a real customer, payment/receipt confirmation, or external sign-off.
2. **Full-scope progress (context only):** keep all stages, including excluded external-only stages, visible and calculate the original full-scope percentage separately when a defined denominator exists. Excluded work is **not complete**; label it “excluded from actionable denominator / externally blocked,” not PASS or done.

For the current A0–A4 tracker, A3 (real commercial pilot, customer acceptance, receipts/cost reconciliation) and A4 (supervised-pilot autonomy/reliability baselines that depend on real operational data) are outside the agent-actionable denominator. Do not hard-code stale stage percentages in this rule file: read the latest dated calculation in `docs/00_START_HERE/CURRENT_STATUS.md` and reconcile it with `docs/00_START_HERE/CURRENT_PRIORITIES.md` and the current master handoff. As of 2026-10-14 after PR #1123, A2 is 10/12 = 83.3%; actionable progress is (100% + 30% + 83.3%) / 3 = 71.1% (71%), and full-scope context is (100% + 30% + 83.3% + 0% + 0%) / 5 = 42.7% (43%). These are rubric-based indicators, not commercial readiness. Never inflate stage-level percentages merely because a stage is excluded from the denominator. If A2 later contains a criterion requiring unavailable external infrastructure, split that criterion out explicitly rather than excluding all locally/CI-testable A2 work.

A green GitHub-hosted CI run is available engineering evidence, not proof of external production, provider, customer, revenue, or deployment outcomes. State the exact SHA and workflow scope. Recompute both figures whenever accepted criteria change and update this file plus the canonical status/handoff documents in the same work checkpoint.


## Current progress accounting — 2026-10-14 after PR #1124

The latest verified checkpoint is PR #1124: tested head `db7ad80181c56dc000aa8662dd467544c8192b31`, squash merge `42cb0024a79ddeff79d5a5ad029dc0c98baf1967`. All 11 required workflow groups passed on the exact tested head. Marketing Manager `workforce_prepare_growth_report` has deterministic real-stack lifecycle evidence; see https://github.com/ijoolaie/AI-Employee/actions/runs/38529979935.

Current role coverage is A2 11/12 = 91.7%. The only role still lacking canonical WorkItem → assignment → dispatch → worker → successful Run evidence is `ai_sales_lead_generation`. A0/A1/A2/A3/A4 = 100/30/91.7/0/0; actionable progress is 73.9% (74%), full-scope context is 44.3% (44%). These are rubric-based indicators only. Live providers, production deployment/outcomes, customer acceptance, and revenue remain unproven. For the next checkpoint, update this rule file and canonical status/handoff documents together whenever accepted criteria or progress changes.
## Progress checkpoint — A1 role audit continued (2026-10-14)

Source-only trace now also covers `ai_seo_growth_employee` and `ai_customer_success`. Their role contracts declare named operations, but the inspected semantic handlers persist tenant-scoped artifacts and report `provider_execution=not_configured`; they do not establish live SEO/search-performance or customer-support integrations. This turn did not execute tests, so no test pass or A1 score increase is claimed. A0/A1/A2/A3/A4 remain 100/30/100/0/0; actionable progress 77%; full-scope context 46%. Continue with the Software Developer contract-to-handler trace, then inspect role-specific tests before selecting a bounded implementation.
## Progress checkpoint — Software Developer provider boundary (2026-10-14)

The source audit now also traces the Software Developer provider selector. Runtime defaults to fail-closed `none`; the contract-test adapter is non-executing; GitHub read-only supports CI status; the GitHub adapter supports CI status and potentially external branch creation only. GitHub provider support does not mean tests/build/deploy/rollback are executed. No tests were run in this source-inspection increment; A0/A1/A2/A3/A4 remain 100/30/100/0/0 (actionable 77%, full-scope 46%). Next, inspect exact role-specific tests for Software Developer, SEO & Growth and Customer Success before selecting a bounded implementation.


## Progress checkpoint — GitHub engineering response-contract hardening merged (2026-10-14)

PR [#1137](https://github.com/ijoolaie/AI-Employee/pull/1137) merged after all 18 check runs passed on exact tested head `27b176b3e0020388d45ab04e13ef7f5c138bdd09`; squash merge: `6ae34445f7eabef8dc8cf8a5926b21d7cdc3dfac`. The GitHub branch provider now validates lookup/create response object SHA contracts and rejects malformed response shapes or a created SHA that differs from the requested source SHA. Three regression cases cover malformed lookup JSON, malformed create JSON, and SHA mismatch. A malformed/mismatched successful HTTP response is reported as an unverified provider outcome, not proof that no external side effect occurred. No live GitHub provider operation or production integration is claimed. Phase indicators remain A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable 77%; full-scope 46%. Next bounded increment: inspect and harden the read-only GitHub CI-status adapter's transport failure, malformed-response and missing tenant-to-repository mapping paths, preserving fail-closed behavior and no write side effects.


## Progress-accounting checkpoint — PR #1146 — 2026-10-14

PR [#1146](https://github.com/ijoolaie/AI-Employee/pull/1146) squash-merged as 088fefd65832020476638ffef45b8bde04717410 from exact tested head 7064dbb340a10e550268ac6421f1582432251940; all 13 check runs passed on that exact head. The regression test asserts that the GitHub engineering provider does not execute git_commit_proposal: it returns not_configured and executed=False. This protects the fail-closed boundary; it does not implement Git commits or prove live GitHub integration.

### Why the headline percentage appears stuck

The current actionable score is (A0 + A1 + A2) / 3. With A0/A1/A2 = 100/30/100, the result is 76.67%, rounded to 77%. A2 is already saturated at 100%, so additional tests inside already-counted role/lifecycle scope do not raise the phase score. A1 remains 30% until the broad, source-and-test-backed all-role capability audit meets its evidence threshold. A3/A4 remain 0%; they are excluded from the actionable denominator but included in full-scope context, currently 46%.

This is a coarse phase-level metric, not a PR-count or engineering-velocity metric. The work is real but mostly hardens contracts and negative paths inside phases already counted. Do not inflate the score merely because PRs merge. Keep the headline score unchanged until exit criteria are met, while reporting each bounded increment separately.

### Next measurable work

1. Trace Software Developer approval end-to-end: role contract → Tool Registry and permissions → persisted approval request/decision → runtime governance → adapter dispatch → provider result and audit. A requires_approval flag or proposal artifact alone is not proof of approval.
2. Build an evidence matrix for every workforce role and operation, recording contract, registry/license, semantic handler, governance/approval, provider support, persisted result/audit, positive and negative tests, exact-head CI, and external validation separately.
3. Define explicit A1 exit criteria and a stable operation-level denominator before revising any score. Fix only confirmed mismatches; preserve fail-closed controls.

Metrics unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable 77%; full-scope context 46%. No live provider write, production readiness, or commercial readiness is implied.


## 2026-10-14 checkpoint — PR #1148 approval-gated workforce resume

- PR #1148: https://github.com/ijoolaie/AI-Employee/pull/1148; merged as `0a38c57cb80f80ae6a522eac8933d0f7b4fc8ddd` from exact tested head `e7f308e2bea13dee5ad3e22da8e7b2a7210feb8b`.
- Verified 13 GitHub Actions workflow runs on that exact head; all 13 completed successfully. This includes CI, CodeQL, architecture, security/privacy, semantic real-stack E2E, W1 control-plane E2E, infrastructure, observability, rollback/alerting, and failure recovery.
- Runtime governance now permits an approval-required workforce operation only when the canonical Run resume path supplies a persisted approval matching tenant, Run, registered tool, tool-call ID, approved status, and exact arguments. Calls without approval context remain fail-closed; argument mismatch is rejected. Central Tool Registry approval enforcement remains in place as a separate boundary.
- Scope/evidence boundary: automated tests and CI only. The provider still returns `not_configured` for `git_commit_proposal`; no actual GitHub write, live provider operation, deployment, or production readiness is established. If a remote write is accepted but its response cannot be read, the external outcome may remain unverified.
- Why progress scores did not move: this fix closes one evidenced approval-resume mismatch, but does not complete provider support or the role-by-role evidence matrix. Do not infer broad A1 readiness from PR count.
- Metrics unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%; full-scope context 46%.
- Next: build and maintain an operation-level evidence matrix across roles (role contract, Tool Registry/permissions, semantic handler, persisted approval/governance, provider support, persisted result/audit, positive/negative tests, exact-head CI, and external validation). Fix only confirmed gaps; keep A1 at 30% until its documented evidence threshold is met.

## 11. Mandatory open GitHub PR and issue triage on every agent run

**Scope:** this repository, `ijoolaie/AI-Employee`. This is a recurring per-run requirement, not an optional cleanup task. Perform it at the beginning of every new task and every continuation/resume (including “continue” / «ادامه بده»), before selecting unrelated implementation work.

### Inventory and evidence

1. Query GitHub's live state for **all open pull requests and all open issues** in this repository. Do not rely on an old handoff, memory, a recent-items list, or the local clone as a complete inventory. Follow pagination/limits until the inventory is complete; if the tools cannot return the full set, report the exact coverage limitation and do not call it a full review.
2. For each open PR, inspect its current base/head and exact head SHA, changed files/diff, linked issues/dependencies, requested reviews/review threads, and required workflow/check results on that exact head. Re-check live state before any mutation.
3. For each open issue, read its title/body, labels, comments and linked PRs where available. Identify the acceptance criteria, latest verified evidence, owner/dependency, and whether it is an engineering task, intentional external gate, upstream-watch item, duplicate, or already resolved.
4. Avoid duplicate work: map issues to their PRs/branches and group related blockers. Prioritize security/correctness, broken required checks, stale/unblocked work, and canonical project priorities.

### Required disposition for every item

Every reviewed open item must receive an explicit, evidence-based disposition recorded in the appropriate GitHub thread or canonical tracker when the review changes or clarifies status:

- **PR:** merge only when policy-required reviews/checks and acceptance criteria pass on the exact current head; otherwise revise, request changes, close with a reason, or hold/defer with a named blocker and next action.
- **Issue:** act now (with a bounded change/PR), keep open and track a concrete next action, defer/hold with a specific dependency and recheck trigger, or close only when verified complete, duplicate, invalid, or superseded. Preserve intentionally open external/customer/production certification gates; never close them merely to reduce the open count.
- For every held/deferred item, record why it cannot progress now, what evidence or event unblocks it, and the next action/recheck condition. For completed work, link the exact commit/PR/test evidence. Update existing canonical status/handoff documents when project status or priorities change; do not create redundant status files.

### Safety and truthful completion

- Never merge a PR solely because its title/body says ready, CI is green without required acceptance, or the queue is old. Never bypass branch protection, reviews, or required checks.
- Do not automatically close issues or merge PRs just to make the list empty. Preserve scope, user data, uncommitted changes, production/release gates, and the repository's security/tenant-isolation constraints.
- Re-check current state and exact SHA immediately before merge/close/update actions; stop if the head moved or evidence is stale.
- Do not claim “all PRs/issues reviewed” unless every currently open item was inspected. Report counts inventoried/reviewed, explicit dispositions, changed items, blockers, and any unreviewed remainder.
- The review is not complete until every open PR and issue has a recorded disposition (including “hold with reason and next action”), and the next highest-priority actionable item is selected. Continue with that item after triage when safe and within the user's task; do not stop after producing an inventory alone.

