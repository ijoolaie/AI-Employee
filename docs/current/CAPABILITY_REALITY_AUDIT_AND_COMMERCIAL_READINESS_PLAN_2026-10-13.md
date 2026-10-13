# AI Employee — Capability Reality Audit & Commercial Readiness Plan

**Created:** 2026-10-13  
**Status:** ACTIVE — evidence-first audit; no production readiness or revenue claim  
**Repository:** `ijoolaie/AI-Employee`  
**Purpose:** separate what is documented/designed, what is implemented, what is tested, what is proven on a real target, and what demonstrably creates revenue.

## 1. Non-negotiable evidence rules

1. A role name, tool schema, UI control, mock provider, or roadmap item is not proof that an end-to-end capability works.
2. Passing CI/CodeQL/Playwright is evidence only for the exact commit, workflow, environment, and scope tested.
3. A published/certified release is not proof of external deployment, live provider access, customer acceptance, or realized revenue.
4. Mark a capability **Verified in execution** only when the evidence identifies the exact commit, test/run or reproducible command, environment, observed outcome, and relevant negative/failure cases.
5. Record missing evidence as **Unknown / not verified**, not as a failure and not as a success.
6. Do not merge or release changes solely because documentation claims them complete. Reconcile against current GitHub state and exact-head checks.
7. External side effects (publishing, outbound messaging, spend, payment/refund, account mutation) require explicit authorization, bounded permissions, idempotency, audit, and a recoverable failure path.

## 2. Current evidence-based baseline

- Latest published and exact-SHA certified release documented by the release ledger: `v1.4.17`, SHA `b403c0dcdea579e017738a6fdea138c2b1a2999c`, certification run `37625345534`, job `112805570856`.
- This is a release certification fact, **not** proof of current `main` being certified.
- External production deployment: **not verified / not claimed**.
- External customer acceptance and realized revenue: **not verified**.
- World viewport framing has bounded desktop/mobile screenshot acceptance recorded for PR #1071; that does not mean the broader World visual redesign, authored 3D assets, obstacle-aware pathfinding, or commercial workflows are complete.
- PR #1072 adds a bounded procedural glass-partition visual change. Its PR description says manual desktop/mobile visual acceptance is pending; do not infer acceptance from build or automated checks.
- Current source-of-truth files had drifted: the manifest still described a September release-candidate checkpoint, the gap register described v1.4.11, the evidence index described v1.4.11, and status/priority documents carried stale PR-review language. The immutable v1.4.17 release facts themselves remain distinct from these stale current-state summaries.

## 3. Why documentation drifted — working root-cause assessment

The evidence supports a process/design failure more than a single typo:

- **Multiple manually maintained truth surfaces:** README, manifest JSON, versioning truth, release ledger, evidence index, gap register, roadmap, current status, and priorities repeat related fields independently.
- **No enforced reconciliation gate:** no evidence reviewed so far shows a mandatory CI check that compares the current release identity, current PR state, reconciliation date, and key status assertions across these documents.
- **Historical checkpoint accumulation:** dated notes are intentionally preserved, but current and historical text are not always clearly separated. A reader can mistake an older snapshot for present truth.
- **Different update cadence/ownership:** release publication was updated in the README/release ledger, while the manifest and operational evidence documents were not updated in the same change set.
- **Ambiguous meanings of “certified/current”:** release certification, current engineering HEAD, PR exact-head CI, production deployment, and customer acceptance are separate states, but copied summaries can blur them.
- **PR state snapshots age quickly:** text such as “merge follows review” remains in a file after the PR has merged unless a later reconciliation explicitly replaces it.
- **Likely missing completion checklist:** no consistent evidence was found in these documents that every status-changing PR must update all authoritative summaries and verify that old statements are historical.

These are evidence-based process hypotheses, not proof of author intent. During this audit, inspect workflows, contribution templates, and PR history before treating any one cause as definitive.

## 4. Status vocabulary for the role-by-role audit

Use exactly one primary status per capability:

- **DESIGNED** — spec/role/tool contract exists; no implementation proof yet.
- **IMPLEMENTED** — executable code exists; end-to-end behavior not yet verified.
- **TESTED-ENGINEERING** — reproducible test/CI evidence exists for a stated scope.
- **VERIFIED-REAL-TARGET** — successful run against the intended live service/target with captured evidence.
- **PARTIAL** — some steps work but the promised workflow is incomplete.
- **BLOCKED** — a named dependency, credential, policy, provider, or defect prevents the next acceptance step.
- **NOT-VERIFIED** — evidence is insufficient; do not infer pass/fail.
- **ACCEPTED** — explicit acceptance criterion and reviewer sign-off exist for the stated scope.

Each row must also record: owner/role; user-visible promise; entry point; implementation files; tool/provider dependency; authorization boundary; positive tests; negative/failure tests; current exact SHA; evidence links/artifacts; human intervention; known gaps; next smallest acceptance test.

## 5. Audit sequence

### A0 — Reconcile truth surfaces (first)

- [ ] Update the current manifest and make its release-vs-engineering-vs-production distinctions explicit.
- [ ] Reconcile the gap register and evidence index to v1.4.17 while preserving v1.4.11 data only as historical evidence.
- [ ] Remove or label stale current-state statements in status and priorities; retain dated history as history.
- [ ] Add this audit plan to the documentation index / start-here path.
- [ ] Inspect PR #1067/#1071/#1072 exact state and the PR/CI workflow that produced stale statements.
- [ ] Add a repeatable consistency check or checklist so this drift is caught before merge.

### A1 — Map every employee role to real execution

Start with: orchestrator/manager, developer, graphic designer, content producer/editor, marketing/advertising, sales/lead generation, customer support, finance/analytics, operations/reliability, HR/recruiting, and any other role claimed in the current role catalog.

For each role, trace:
role definition → allowed operation → registered tool → concrete implementation → provider/credential → execution path → persisted result/audit → UI/report → failure handling → acceptance test.

Do not assume the list above is the complete roster; discover the canonical role catalog and reconcile every role in it.

### A2 — Test the highest-value workflows

1. **Content:** brief → draft → review → asset generation → authorized publication → verify publication → performance data.
2. **Graphic design:** brief → image/design provider call → asset persisted → provenance/licensing recorded → preview/revision → export/delivery.
3. **Marketing:** target segment → campaign proposal → approval/budget guard → execution → attribution → stop/rollback.
4. **Sales:** lead discovery → qualification → approved outreach → response handling → proposal/checkout → payment confirmation → CRM/audit update.
5. **Customer delivery:** paid/authorized order → service execution → quality check → delivery confirmation → support/repair path.
6. **Finance/analytics:** provider costs + refunds/fees + recognized receipts → reconciled unit economics; do not use simulated data as realized revenue.
7. **Developer/operations:** issue → bounded code change → tests/review → exact-head workflows → controlled deployment/rollback; no silent self-merge or self-approval.

For each workflow, test success, provider timeout, invalid response, denied permission, duplicate/replay, partial failure, retry, cancellation, and recovery.

### A3 — Commercial launch gates

- [ ] Select one narrow, deliverable service and define a specific customer segment.
- [ ] Confirm a real provider and live credentials are configured safely.
- [ ] Confirm price, terms, privacy, refund/support, and lawful outreach policies.
- [ ] Run a human-supervised pilot with at least one real customer before claiming market validation.
- [ ] Record actual receipts, refunds, provider/API costs, advertising spend, labor/operations cost, and gross contribution.
- [ ] Verify delivery and customer acceptance independently of the agent's own success message.
- [ ] Only then automate bounded steps, preserving human approval for financial, legal, reputational, and irreversible actions.

### A4 — Autonomy and reliability acceptance

Track at minimum: workflow completion rate; independently verified success rate; human-intervention rate; provider failure/retry rate; duplicate side effects; escaped defects; mean time to detect/recover; per-task cost; lead-to-customer conversion; delivery acceptance; refunds/complaints; and contribution margin.

Do not set arbitrary targets before establishing a baseline. Agree on targets after collecting a representative supervised pilot dataset.

## 6. Prioritization rule

Fix stale truth surfaces and blockers first; then select the shortest end-to-end path to one paid, deliverable service. Do not expand the employee roster or build broad autonomy before a narrow workflow is proven. UI/World work may continue in its own lane, but must not be represented as commercial readiness evidence.

## 7. Audit log

| Date | Area | Finding / action | Evidence | Status |
|---|---|---|---|---|
| 2026-10-13 | Documentation truth | Identified stale manifest, gap register, evidence index, and status/priority snapshots; reconciliation proposed in this PR | README, manifest, release ledger, gap register, evidence index, current status/priority | IN PROGRESS |
| 2026-10-13 | Commercial readiness | External deployment, customer acceptance, and realized revenue are not verified in repository evidence | README; Versioning Truth; Release Truth Ledger | OPEN |
| 2026-10-13 | World | PR #1071's viewport criterion is bounded acceptance only; PR #1072 remains a separate visual candidate pending manual review per PR description | Current Status; PR #1071; PR #1072 | OPEN |

## 8. Exit criteria

The audit is not complete until every canonical role has a status row, every priority workflow has exact reproducible evidence or an explicit gap, stale current-state statements are reconciled, and a narrow commercial pilot has independently verifiable customer/delivery/financial evidence. A green CI run alone cannot satisfy these exit criteria.
