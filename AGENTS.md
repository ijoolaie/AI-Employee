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
