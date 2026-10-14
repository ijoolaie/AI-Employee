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

For the current A0–A4 tracker, A3 (real commercial pilot, customer acceptance, receipts/cost reconciliation) and A4 (supervised-pilot autonomy/reliability baselines that depend on real operational data) are outside the agent-actionable denominator. Do not hard-code stale stage percentages in this rule file: read the latest dated calculation in `docs/00_START_HERE/CURRENT_STATUS.md` and reconcile it with `docs/00_START_HERE/CURRENT_PRIORITIES.md` and the current master handoff. As of 2026-10-14 after PR #1119, A2 is 8/12 = 66.7%; actionable progress is (100% + 30% + 66.7%) / 3 = 65.6% (66%), and full-scope context is (100% + 30% + 66.7% + 0% + 0%) / 5 = 39.3% (39%). These are rubric-based indicators, not commercial readiness. Never inflate stage-level percentages merely because a stage is excluded from the denominator. If A2 later contains a criterion requiring unavailable external infrastructure, split that criterion out explicitly rather than excluding all locally/CI-testable A2 work.

A green GitHub-hosted CI run is available engineering evidence, not proof of external production, provider, customer, revenue, or deployment outcomes. State the exact SHA and workflow scope. Recompute both figures whenever accepted criteria change and update this file plus the canonical status/handoff documents in the same work checkpoint.
