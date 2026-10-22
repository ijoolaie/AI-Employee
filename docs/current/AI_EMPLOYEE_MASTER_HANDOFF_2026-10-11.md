## AI-Employee handoff update — PR #1175 merged; local stack ready for image refresh (2026-10-15)

### Verified repository and fix state
- PR [#1175](https://github.com/ijoolaie/AI-Employee/pull/1175) was squash-merged on 2026-10-15 as [`8c1067a030f3aff7d54d3fdee64a664ea0bc3bae`](https://github.com/ijoolaie/AI-Employee/commit/8c1067a030f3aff7d54d3fdee64a664ea0bc3bae).
- Exact PR head: `9a05e5ad2a232aebfaf3fdcca04a9ddce8194d88`; all 15/15 reported check-runs succeeded, including backend, frontend, semantic E2E, infrastructure, security/privacy, DAST, recovery, architecture, observability, tenant isolation/RBAC, CodeQL and `w21-real-stack`.
- Changed `backend/app/services/file_service.py`: tenant quota serialization now uses SQLAlchemy `with_for_update(key_share=True)`, which on PostgreSQL emits `FOR NO KEY UPDATE`. This still serializes competing quota writers while allowing the foreign-key `KEY SHARE` check used by independent `ai_provider_calls` inserts.
- Added `backend/tests/test_file_service_locking.py` to assert the PostgreSQL lock SQL contract.
- Root cause is strongly indicated by the earlier captured PostgreSQL wait: an `ai_provider_calls` insert waited on a tenant-row key-share check while the Run transaction held the tenant row lock during tool/file work. The fix has CI evidence; the local CSV end-to-end behavior is NOT yet verified.

### Local machine and Docker evidence (user-provided, 2026-10-15)
- Working copy: `C:\Users\Ali\AI-Employee`; branch `main`; `git pull --ff-only origin main` advanced from `72aa2093` to `8c1067a0`; `git status --short` was empty.
- Compose stack from `docker-compose.yml`, `docker-compose.local-production.yml`, and `%TEMP%\ai-employee-local-ports.override.yml` is running:
  - API: `127.0.0.1:18000->8000`, healthy.
  - Frontend: `127.0.0.1:13000->3000`, healthy.
  - PostgreSQL 16: `127.0.0.1:15432->5432`, healthy.
  - Redis 7: `127.0.0.1:16379->6379`, healthy.
  - Worker: running (Docker reports Up; no health status shown).
  - Worker-control: running (created 7 days ago; Up 4 hours at inspection).
- All six containers showed they had been created about four hours before the inspection, while the Git pull just brought the fix into the host checkout. Therefore the running API/Worker images may still contain pre-fix code. Do not create another Run until API and Worker are rebuilt/recreated from current `main`.

### Blocker reproduction and test target
- Earlier Run attempts reached LM Studio successfully (`google/gemma-4-e4b`, base URL `http://host.docker.internal:1234/v1`, chat-completions HTTP 200), but failed after waiting about 300 seconds during durable provider-call insertion/commit. Worker retry then skipped the idempotent Run. Do not count placeholder/deterministic certification output as real dataset analysis.
- CSV test file: `report-analyst-test.csv`, file ID `0a74b684-7841-4079-96e6-e08af4003286`, 73 bytes.
- Expected real results:
  - Book A: 10 × 120 = 1200
  - Book B: 5 × 200 = 1000
  - Book C: 8 × 75 = 600
  - Total units = 23; total revenue = 2800.
- Existing local test tenant: `raya-test-org`, UUID `f2ed7c1d-002f-443a-8657-0d1ca4f70132`. Local test license included `employee.run` and `tool:analyze_dataset`, active through 2026-11-14 at the last recorded inspection; re-check only if the API rejects the Run.
- Next bounded procedure: (1) rebuild/recreate only API and Worker using the exact same Compose file list; (2) verify they are running from current source/image and check health/logs; (3) execute one `analyze_dataset` Run against the existing CSV; (4) verify terminal Run status, absence of tenant/FK lock wait, and the actual result/artifact. If it fails, capture Run ID plus Worker/Postgres logs before changing anything else. Keep external server/production tests excluded from progress calculations.

### Progress and evidence boundary
- Current operational progress tracker: 78% (unchanged until the local real-tool Run succeeds).
- Full product-scope coverage: 46%.
- Rubric coverage A0/A1/A2/A3/A4: 100% / 30% / 100% / 0% / 0%.
- Historical agent-actionable rubric in prior handoffs is 77%; do not conflate that separate rubric with the current operational tracker at 78%.
- PR merge and 15/15 CI checks are confirmed; local container refresh, real CSV execution, artifact verification, production deployment, release certification, and customer acceptance are NOT confirmed.
- Certified release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c` unless a separate release certification proves otherwise. PR #1175 is an engineering fix, not a new certified release.

---

## Handoff update — PR #1160 merged (2026-10-14)

### Verified completion
- PR [#1160](https://github.com/ijoolaie/AI-Employee/pull/1160) squash-merged as [`5e451a5c3891edaa59b6616e3ba1a4c5cd9a97cd`](https://github.com/ijoolaie/AI-Employee/commit/5e451a5c3891edaa59b6616e3ba1a4c5cd9a97cd) from exact tested head [`0ee845eb4499234db653e96e51264e07cca254fe`](https://github.com/ijoolaie/AI-Employee/commit/0ee845eb4499234db653e96e51264e07cca254fe); all 17 check-runs passed.
- Ambiguous branch-create outcomes trigger one read-only GET of the exact ref. If the ref points to the requested source SHA, return `reconciled`; if it points elsewhere, return `conflict`; if it is missing, malformed, or unavailable, preserve `outcome_unknown`. The POST is never blindly retried.
- Regression tests cover exact-SHA reconciliation, 404 preserving unknown outcome, mismatched-SHA conflict, malformed create responses, stream failures, and server errors.

### Evidence boundary and next work
This is mocked-test and CI evidence only. It does not prove live GitHub mutation, configured production credentials, or production readiness. The provider still supports CI-status reads and branch creation only; Git commit, PR creation, deploy, and rollback are unsupported. Next: continue the existing role-operation trace only to a concrete, reproducible gap, then separately arrange supervised verification of operator configuration before any live write. Keep rubric unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable 77%; full scope 46%.

---

## Handoff addendum — PR #1157/#1158 provider outcome audit (2026-10-14)


### Completed
- PR #1157 adds regression coverage that the semantic handler preserves `outcome_unknown`, `provider_execution`, `executed=False`, `external_side_effect=True`, and the provider reason.
- PR [#1158](https://github.com/ijoolaie/AI-Employee/pull/1158) squash-merged as [`e77ff28441266b8b2acf2489f9d9ddbbf0bd11fe`](https://github.com/ijoolaie/AI-Employee/commit/e77ff28441266b8b2acf2489f9d9ddbbf0bd11fe), from exact tested head `05349f23eb02c5d96e141439c836e2050d4de1d3`. All 16/16 check-runs succeeded.
- Run-service audit records preserve allowlisted provider outcome fields, and the audit event status reflects `outcome_unknown` rather than `success`. Normal execution and approved-tool resumption are both covered. Provider reason is capped at 500 characters; arbitrary payloads/raw arguments are not copied.

### Remaining / evidence boundary
- Implement safe read-after-write reconciliation for an ambiguous GitHub branch-create POST before permitting retries. Verify repository, branch, and expected SHA rather than treating any branch lookup as proof.
- Automated checks do not prove a live GitHub mutation or production configuration.
- Provider remains limited to CI-status reads and branch creation. Git commit, PR creation, deploy, and rollback are unsupported.
- Progress rubric unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable 77%; full-scope 46%.

---

## Handoff addendum — PR #1155 merged (2026-10-14)

### Completed
- PR [#1155](https://github.com/ijoolaie/AI-Employee/pull/1155) squash-merged as [`6947679d0fe89e8c81584f19ba2560480eb336b0`](https://github.com/ijoolaie/AI-Employee/commit/6947679d0fe89e8c81584f19ba2560480eb336b0), from exact head `eca8e2fa5bdbfcb8279f1f415d02ed64cc947aaf`.
- Exact-head evidence: 17/17 check-runs and 14/14 workflow runs passed.
- Branch-create ambiguous outcomes are now represented as `outcome_unknown` for response-stream/transport failures, invalid create responses, SHA mismatch, and HTTP 5xx. The concurrent-create 422 case remains a conflict; preflight lookup failures remain provider errors.

### Evidence boundary and follow-up
This change prevents a false claim of definitive failure; it does not automatically reconcile the remote branch. Before retrying an `outcome_unknown` result, callers should perform a read-after-write lookup and verify the branch ref and target SHA, while treating mismatches as a reconciliation issue rather than blindly repeating POST. Current tests use mocked HTTP; they do not prove live GitHub writes or production configuration.

The provider supports CI-status reads and branch creation only. Commit, PR creation, deploy, and rollback execution remain unsupported. Keep progress rubric unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable 77%; full-scope 46%.

Next bounded task: inspect caller/runtime handling for `outcome_unknown` and implement/test reconciliation only if the public execution path currently permits unsafe retry or loses the uncertain state.

---

## Handoff addendum — PR #1152 and #1153 (2026-10-14)

### Completed
- PR #1152 merged: corrected GitHub branch-reference lookup route; merge commit `398cddef834c1d845cce0352ea5aeccb7f4d3dc4`.
- PR #1153 merged: strengthened Git branch ref validation for hidden/trailing-dot and `.lock` components and `@`; exact head `21723a046957b3c0ee56579e901ec768390ea605`, 17/17 successful check-runs, merge commit `a3746d8f18271549c979f0fa0c104bc34dd51e67`.

### What this does not prove
Automated CI/test evidence is not proof of live GitHub writes, operator configuration, production deployment, or release readiness. The configured provider implements CI-status reads and branch creation only. Commit/PR/deploy/rollback execution remains unsupported by this adapter.

### Next bounded task
Continue the Software Developer role-operation audit. Trace approval identity and denial, registry binding/permissions, provider capability, error handling, and persisted results. File a fix only when the source and tests establish a concrete defect. Keep progress rubric unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable 77%; full-scope 46%.

---

## Progress checkpoint — PR #1150 workspace-key collision fix merged (2026-10-14)

- PR [#1150](https://github.com/ijoolaie/AI-Employee/pull/1150) was squash-merged into `main` as [`5bd31f8823d83e1cbb00515ed80ada2b4d4c2ca7`](https://github.com/ijoolaie/AI-Employee/commit/5bd31f8823d83e1cbb00515ed80ada2b4d4c2ca7) from exact tested head [`7335e2d90bfd0057560343794c168a59b6fd2e81`](https://github.com/ijoolaie/AI-Employee/commit/7335e2d90bfd0057560343794c168a59b6fd2e81).
- Exact-head evidence: 27/27 commit check-runs concluded success. [Workforce Semantic Real-Stack E2E run 38583617654](https://github.com/ijoolaie/AI-Employee/actions/runs/38583617654) passed, including deterministic real-stack startup, migration graph verification, deterministic market provider, the semantic workforce matrix, diagnostics collection and shutdown.
- The fix replaces lossy slash-to-underscore workspace key mapping with a SHA-256-derived key based on the normalized logical path. Regression coverage asserts distinct keys and independent readback for paths such as `src/app.py` and `src_app.py`; the E2E lookup was corrected to validate persisted workspace payloads by logical path and content rather than assuming the old key format.
- Evidence boundary: this establishes the merged source fix and automated CI/real-stack test evidence only. It does not establish live GitHub write execution, external provider execution, deployment, production readiness, customer acceptance, or a new release certification.
- Progress rubric unchanged: A0/A1/A2/A3/A4 = 100/30/100/0/0; agent-actionable progress 77%; full-scope context 46%. One additional correctness defect is fixed, but the broad A1 role/operation evidence threshold is not met, so do not raise the rubric scores.
- Follow-up: continue the source/test-backed role-operation audit through role contract → Tool Registry/permission → semantic handler → approval/governance → provider → persisted result/audit and positive/negative tests. In particular, do not equate `git_commit_proposal` role binding with actual Git commit execution: provider support remains `not_configured`.
- PR metadata reconciliation: the stale “CI is pending” wording in PR #1150 was corrected after exact-head checks passed.

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

---

## Handoff checkpoint — 2026-10-14: website health provider merged; A1 audit continues

### Verified completion
- PR [#1132](https://github.com/ijoolaie/AI-Employee/pull/1132) merged as [`5c62de7a399250332716dc714bd9f53d09bfce38`](https://github.com/ijoolaie/AI-Employee/commit/5c62de7a399250332716dc714bd9f53d09bfce38), from exact tested head `5e0d34df85021be1ddfc24aa551e12a6aa25911d`. It proves persisted caller-supplied SEO research context, not external search-engine execution or SEO outcomes.
- PR [#1135](https://github.com/ijoolaie/AI-Employee/pull/1135) squash-merged as [`dce5371656fba372b0df06f3c25a010fdbb7e747`](https://github.com/ijoolaie/AI-Employee/commit/dce5371656fba372b0df06f3c25a010fdbb7e747) from exact tested head [`cd8414eea9dc483aaa0a9fb75dbf21a49f5e5c54`](https://github.com/ijoolaie/AI-Employee/commit/cd8414eea9dc483aaa0a9fb75dbf21a49f5e5c54). All 32 check runs passed on that exact head.
- The merged website health path is read-only and tenant-scoped. It uses operator-configured HTTPS targets, bounded timeouts, disabled redirects, URL safety validation and persisted health evidence.

### Evidence boundary
- No live website target is configured or verified by this code change; production website health remains unproven.
- Website preview/build/deploy/rollback is not implemented by this increment. A passing CI suite does not establish production deployment, customer acceptance or revenue.
- A0/A1/A2/A3/A4 remain 100/30/100/0/0; actionable 77%; full-scope 46%.

### Ordered next actions
1. Continue the source/test-backed A1 role-by-role capability audit, tracing operations through provider selection, tenant-scoped persistence, authorization/approval and negative paths.
2. Select the next bounded implementation only after source review identifies a concrete gap and its tests/acceptance criteria.
3. Validate real provider configuration and operational/release gates separately; keep A3/A4 externally gated until real pilot/operational/customer evidence exists.

---

## Latest verified handoff — 2026-10-12 after PR #1062 merge

The current source of truth is [AI Employee World Master Handoff 2026-10-12](AI_EMPLOYEE_WORLD_MASTER_HANDOFF_2026-10-12.md). PR #1062 merged at `d6e4f9297dbf7122aab22bdf8bbea467a6f8f038` after all five exact-head workflow groups passed for source head `7dd0a54709a6b8660dc7fb3d32051160ac50fbb2`. The earlier artifact had framing issues, corrected by PR #1071. Its exact-head desktop/mobile artifact was reviewed at 1440×900 and 390×844; the full floor is visible in both. Viewport-framing acceptance is met for this bounded criterion; broader visual redesign remains incomplete. See the current World Master Handoff and Visual Follow-up for exact-head evidence.

Do not infer that authored GLB employee models, full pathfinding, foot planting or a production release are complete. Characters remain procedural; collision checks cover static footprints only; latest certified release remains `v1.4.17`.

---

## Latest user direction — 2026-10-12: World visual reference locked

- User supplied two screenshots: current desktop AI Company HQ (before-state) and a portrait mobile office-management tycoon game (target art-direction reference).
- The canonical gameplay specification §30 now records the approved direction and acceptance gates. Use it as the source of truth: warm/cream architecture, coral/terracotta floor accents, teal/blue partitions, windows/blinds, doors/wall decor, coherent detailed workstations, varied stylized employees, soft shadows, readable compact HUD and stable 3/4 isometric composition.
- Treat the target screenshot as inspiration for visual language/readability only. Do not copy proprietary sprites, characters, maps, exact HUD, branding or source. Use original/properly licensed assets and record provenance.
- Implementation order: scene composition and responsive framing; authored/licensed employee and workstation art; obstacle-aware navigation; mobile HUD/accessibility; actual-route desktop/mobile screenshots and regression testing.
- Keep backend employee/run/approval state, tenant isolation, room entitlements, approvals and business metrics authoritative. No fake arcade currency/economy/activity.
- PR #1050 remains Draft/unmerged until the approved visual direction is actually implemented and reviewed in browser screenshots. Documentation update does not mean the redesign is implemented; no release certification is implied.

---
## Latest verified checkpoint — 2026-10-12, World V2 visual review candidate

- PR [#1050](https://github.com/ijoolaie/AI-Employee/pull/1050) is open, Draft and unmerged on current `main`, exact head `8a7de75a8d49b4e1489b00353615f7a1f3808f87`. All five exact-head workflows passed: [CI](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177840), [CodeQL](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177820), [Production Infrastructure Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177945), [HA Failure Recovery Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177822), and [Ephemeral DAST Validation](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177856).
- CI produced artifact `world-visual-review-1e43f2d0cd75d04671bf8b71d9e7f54f848f15ef` with actual Playwright screenshots at desktop 1440×900 and mobile 390×844: [CI run / artifacts](https://github.com/ijoolaie/AI-Employee/actions/runs/38213177840).
- Screenshot review found and corrected a mobile camera inversion, switched screenshots from full-page to exact viewport capture, reduced desktop viewport height to keep controls visible, and hid the mobile status overlay to prevent overlap. The current artifact shows the desktop composition and controls within the target viewport and a coherent mobile view.
- Visual acceptance is **not complete**: most character/furniture geometry remains procedural, facial/prop quality still falls short of the target stylized tycoon look, mobile labels are small, and static collision guards are not full pathfinding. Screenshots are evidence for review, not proof of a finished redesign. Do not merge #1050 until the visual direction is accepted and the remaining art/navigation gaps are resolved.
- PR #1046 was closed unmerged as superseded by #1050. PR #1045 remains closed unmerged after the user rejected its result.
- Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`; these checks do not certify a new release.

---


## Latest verified checkpoint — 2026-10-11 after PR #1040/#1041/#1042 merges

- PR #1040 documentation reconciliation merged at `467e6266540cd429b6e4156ac1a3f9ca00d96759`; CodeQL passed on its final PR head `6a5126d6aad9f88ccd29b91b2e66070272108c7a`.
- PR #1041 merged at `e1633e9bf000af045e2571d930b4eeefec30883f`; exact-head CI, CodeQL, infrastructure, HA recovery and DAST passed. Expired room access remains server-authoritative and fail-closed.
- PR #1042 merged at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`; all 11 exact-head workflows passed, along with backend (1452 passed, 1 deselected), local Docker build, 13 support-message tests, and real PostgreSQL + HTTP API concurrency regression.
- PR #1045 is closed unmerged after the user rejected its local visual result. PR #1046 remains Draft/unmerged; all five workflows passed on exact head `7f456bda345053e3ff2caf7697a1bc2a36199b19`, but actual desktop/mobile browser screenshots and visual acceptance are still missing. The repository has no GLB/GLTF/FBX/OBJ/BLEND or raster image assets; the current renderer remains primitive-built.
- Remaining gates: manual support create/reload/reply/authorized-attachment QA; customer-tenant support entry point tracked by #1043; and authored/licensed World assets plus actual-browser desktop/mobile visual QA tracked by #1044. Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

---

## Latest verified checkpoint — 2026-10-11 after PR #1041/#1042 merges

- PR #1041 merged to `main` at `e1633e9bf000af045e2571d930b4eeefec30883f`. Exact head `528750ce9fbac51690d3da6a660394ed6896cbb8` passed CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST. The server remains authoritative; a renewal order does not itself grant room access.
- PR #1042 merged to `main` at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`. Exact head `4bebbdcdce78dc5e43276cbaa7aac9136c5fdf4e` passed all 11 workflow runs; backend suite 1452 passed, 1 deselected; local Docker build, 13 support-message tests, and real PostgreSQL + HTTP API concurrency regression passed. Manual support workflow/attachment QA is still outstanding.
- PR #1045 was closed unmerged after the user rejected its local visual result. It is not a completed redesign. PR #1046 carries the combined corrective diff against `main`; all five workflows passed on exact head `7f456bda345053e3ff2caf7697a1bc2a36199b19`, but it remains Draft because actual desktop/mobile browser screenshots and user visual acceptance are missing.
- World visual gaps remain: most employee/furniture geometry is primitive-built, collision-aware pathfinding is absent, and overflow staging is not a final design. Preserve the user's rejection as the acceptance boundary; do not merge #1046 as complete until runtime evidence and visual quality are addressed.
- PR #1040 remains the documentation reconciliation PR; its head was updated to record these dispositions and must be validated on its latest SHA. Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

---

# AI-Employee Master Hand-off — 2026-10-11


## World visual redesign — approved art direction and active implementation — 2026-10-11

- The user explicitly approved an Idle Company Tycoon / Agent Office-like visual direction: polished stylized isometric 3D office, friendly varied cartoon employees, detailed workstations and rooms, warm/cool lighting, soft shadows and coherent materials. These games are visual references only; no proprietary assets or source code are to be copied.
- PR [#1045](https://github.com/ijoolaie/AI-Employee/pull/1045) was closed unmerged after the user rejected its local visual result. Its implementation history is included in the combined corrective diff of [#1046](https://github.com/ijoolaie/AI-Employee/pull/1046); do not treat #1045 as a completed redesign.
- Latest noted code commit: `11baed5f53d988addd757e07c88954cbae66d5a6` (moves decorative wall art to side walls so it does not cover rear glazing). Follow-on documentation commits exist on the PR branch; check the current PR head and exact-head workflows before reporting final validation.
- PR #1046 exact head `7f456bda345053e3ff2caf7697a1bc2a36199b19` passed CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST. Automated success does not validate visual quality. Real-browser desktop/mobile screenshots, console/performance inspection, and employee/input/accessibility/room-authorization regression checks remain outstanding. Keep #1046 Draft until those acceptance gates pass.
- Preserve employee selection, keyboard/touch input, accessibility, tenant authorization, fail-closed room expiry/API-error behavior and authoritative room-scene configuration. No release certification changes; latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

## Latest checkpoint — 2026-10-11 16:21 +03:30

### User-observed UI gaps (verified against current source)

- **Customer support entry point:** the generic tenant sidebar shown in the running app has Unified Inbox and Conversations but no support-ticket entry. Those screens represent customer-channel conversations and are not the support escalation workspace.
- The implemented ticket UI is `frontend/app/(reseller)/reseller/support/page.tsx` at `/reseller/support`. The reseller layout guards the route and redirects tenants whose `tenant_kind !== "reseller"` to `/dashboard`; this is why a generic tenant account cannot simply use the reseller page. Do not weaken that guard to make the menu item appear.
- Issue [#1043](https://github.com/ijoolaie/AI-Employee/issues/1043) tracks an authorized customer-tenant support entry and workflow, distinct from Unified Inbox, with tenant-isolated ticket/thread persistence and attachment access. The user has not yet confirmed manual ticket create/reload/reply acceptance in the local stack.
- **World graphics:** `frontend/features/world/WorldViewport.tsx` still constructs the office scene from procedural Three.js primitives (box-based floor tiles, walls, desks and simple procedural characters). PR #1041 is lease-renewal UX only and does not materially redesign the scene. The user's report that the World looks unchanged is consistent with the current implementation.
- Issue [#1044](https://github.com/ijoolaie/AI-Employee/issues/1044) tracks the visual redesign against `docs/blueprint/AI_COMPANY_WORLD_GAMEPLAY_SPEC.md`, requiring actual before/after screenshots at desktop and mobile sizes and regression checks for controls, room authorization and accessibility. Do not claim the redesign is implemented until code changes and screenshots prove it.

### Current open PR disposition (checked at this checkpoint)

- [#1040 docs](https://github.com/ijoolaie/AI-Employee/pull/1040): merged at `467e6266540cd429b6e4156ac1a3f9ca00d96759`; final documentation head CodeQL passed. No runtime test claim.
- [#1041 World lease renewal](https://github.com/ijoolaie/AI-Employee/pull/1041): merged at `e1633e9bf000af045e2571d930b4eeefec30883f`; exact PR head passed CI, CodeQL, Production Infrastructure Validation, HA Failure Recovery Validation and Ephemeral DAST. Functional renewal UX only; visual redesign remains separate.
- [#1042 support attachment concurrency](https://github.com/ijoolaie/AI-Employee/pull/1042): merged at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`. Exact head passed all 11 workflows; backend suite 1452 passed, 1 deselected; local Docker build, 13 support-message tests, and real PostgreSQL + HTTP API race regression passed. No schema/migration changes. This does not solve the missing customer support navigation in #1043.

PR #1041 and #1042 have since been merged as recorded in the latest checkpoint above. The latest certified release remains `v1.4.17`; CI success is not production certification.


## Current verified repository state

- Repository: `ijoolaie/AI-Employee`
- PR #1039 merged at `27c44ac33a92c636e552950cdfa2f983255e40a8`; subsequent merges: #1041 at `e1633e9bf000af045e2571d930b4eeefec30883f` and #1042 at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`. PR #1040 remains open for documentation reconciliation.
- PR #1039 exact tested head: `9febc1124b28f53b8b8b4ba5c09a8f26bb978dfa`; reported CI passed, including isolated PostgreSQL migration/persistence tests, backend tests, frontend lint/build, Playwright browser regressions, CodeQL, DAST, architecture, security/privacy and infrastructure checks.
- Latest published certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`. Engineering merges and green CI are not production deployment or release certification.

## Merged implementation slices

### Reseller support
- #1031: tenant-scoped support escalation message threads.
- #1033: tenant-safe message attachments and participant-scoped downloads.
- #1035: reseller support conversation workspace.
- #1036: persisted reseller-created tickets across page reloads.
- #1039: PostgreSQL-backed HTTP API persistence/tenant-isolation regression plus Playwright reload regression.

Coverage boundary: the Playwright reload regression mocks the API; the backend API regression separately exercises PostgreSQL and tenant isolation.

### AI Company World
- #1016: server-authorized room access gate.
- #1018: validated room scene configuration API.
- #1019: room furniture editor.
- #1021: tenant-scoped employee placements (presentation only).
- #1023: stale layout write protection.
- #1025: audited, dry-run-first legacy room inventory reconciliation.
- #1028: room lease expiry communication.
- #1029: closed as superseded by PR #1041; it was not merged. Its stale branch is not a source of truth.

## Open work / acceptance gates

1. **PR #1041 — renewal UX replacement:** merged at `e1633e9bf000af045e2571d930b4eeefec30883f`. Exact head passed all five automated workflow gates. The backend returns `granted=false, reason=lease_expired` for expired leases. PR #1029 remains closed as superseded and was not merged.
2. **Support manual acceptance:** verify create → reload → reply/thread → attachment download. Automated tests now cover concurrent attachment reuse: PR #1042 exact head `4bebbdcdce78dc5e43276cbaa7aac9136c5fdf4e` passed local Docker unit tests (13 passed) and the real PostgreSQL + HTTP API race regression (1 passed). Still manually test both ticket participants, foreign-tenant denial, deleted/missing files, and count/type/size policy.
3. **World manual QA:** test desktop and mobile viewport, keyboard/touch controls, accessibility, console errors and room lease expiry behavior.
4. **Payments / wallet:** live provider verification, signed/replay-safe callbacks, explicit USDT network policy, and World Credit remain blocked until authoritative verification and a durable append-only ledger with atomic replay-safe accounting are implemented.
5. **Release:** no production certification claim; stay on the documented `v1.4.17` release boundary unless a separately certified release is produced.

## PR disposition

- #1039: merged.
- #1027: closed as an outdated draft; its legacy-inventory feature remains merged in #1025. A current-main documentation reconciliation is tracked in PR #1040.
- #1029: closed as superseded, not merged; PR #1041 is the reconciled replacement and has passed exact-head automated checks.
- #1041: merged at `e1633e9bf000af045e2571d930b4eeefec30883f`; exact-head CI/security/infrastructure/recovery/DAST checks passed.
- #1042: merged at `cd1f218469d913e4e586e8a0c29b00dbb9d246ad`; exact head passed all 11 workflow runs, backend suite (1452 passed, 1 deselected), local Docker build, 13 support-message unit tests, and real PostgreSQL + HTTP API concurrency regression (1 passed). No schema/migration changes.
- #1040: merged documentation reconciliation PR at `467e6266540cd429b6e4156ac1a3f9ca00d96759`; final exact head `6a5126d6aad9f88ccd29b91b2e66070272108c7a` passed CodeQL run `38164377498`.

## Next recommended sequence

1. PR #1042 is merged; next finish manual support acceptance: create → reload → reply/thread → authorized attachment download, including both participants, foreign-tenant denial, missing/deleted files and policy limits.
2. PR #1041 is merged; manually verify expiry/renewal UX and preserve #1028 expiry status plus fail-closed access behavior.
3. Manually validate World Mode expiry/renewal and desktop/mobile behavior; CI is not a substitute for local visual QA.
4. Complete manual support acceptance: create → reload → reply/thread → authorized attachment download, including both participants, foreign-tenant denial, missing/deleted files and policy limits. Concurrency is covered by automated/local PostgreSQL regression.
5. Update this hand-off with observed manual QA results rather than inferred status.


## Current engineering checkpoint — PR #1137 merged (2026-10-14)

- PR [#1137](https://github.com/ijoolaie/AI-Employee/pull/1137) — GitHub branch-provider response-contract hardening — merged at `6ae34445f7eabef8dc8cf8a5926b21d7cdc3dfac`.
- Exact tested PR head: `27b176b3e0020388d45ab04e13ef7f5c138bdd09`; all 18 check runs passed on that exact head.
- Added response-shape and SHA validation for GitHub branch lookup/creation, with regression coverage for malformed lookup payload, malformed create payload, and returned SHA mismatch. A malformed/mismatched response after an HTTP write does not prove absence of an external side effect; the outcome remains unverified.
- No live GitHub provider call, production configuration, deployment, or rollback has been verified. Phase indicators remain A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable 77%; full-scope 46%.
- Next: audit the read-only GitHub CI-status adapter's transport failure, malformed response and missing tenant-to-repository mapping paths; preserve fail-closed behavior and avoid new external writes.

## 2026-10-14 continuation — PR #1162

- **Merged:** PR #1162, merge commit `ed3d27bc22cc3b89752e3f237aac9d68cba15f48`.
- **Exact tested head:** `315c5a4a0e9a40d66275c4a4500519ff3b8f01b3`; all 16 check runs concluded success.
- `_tool_audit_status` now preserves `outcome_unknown` and `reconciled` instead of recording a reconciled result as ordinary `success`. A `reconciled` outcome means one read-only GET confirmed the requested branch ref and SHA after an ambiguous POST response. It does not claim the current invocation created the branch and does not retry the POST.
- **Evidence boundary:** automated tests and CI only. No live GitHub mutation, production credentials/configuration, deployment, rollback, or production readiness has been verified. Keep progress at actionable 77%, full-scope 46%, A0/A1/A2/A3/A4 = 100/30/100/0/0 until broader evidence supports a change.


## 2026-10-14 continuation — PR #1164

- **Merged:** PR #1164; merge commit `245beb6b335a794bb0220d2d17a87f61f205e6ab`.
- **Exact tested head:** `229a57a67ce7022403d64a980c8e06e13d18c6b9`; all 17 check runs succeeded on that exact SHA.
- The initial GitHub branch lookup now requires exact `refs/heads/{branch_name}` identity and a valid SHA. A response for a different ref returns `provider_error` and does not proceed to POST; regression test covers this no-write behavior.
- **Evidence boundary:** automated tests/CI only. No live GitHub mutation, production credentials/configuration, deployment, rollback, or production readiness has been verified. Metrics unchanged: actionable 77%; full-scope 46%; A0/A1/A2/A3/A4 = 100/30/100/0/0.
- **Next:** plan a supervised, explicitly authorized external validation of the supported `git_branch` operation in a disposable test repository/branch, with configured credentials and a cleanup plan. Until then, keep live-write status unverified.


## 2026-10-14 continuation — PR #1166

- **Merged:** PR #1166; merge commit `4de70b6389e012d9416818c837287cc900a3ed6c`.
- **Exact tested head:** `61d46b1fdfee2792db694da5fed4549b64404f6e`; all 13 check runs passed after rerunning the frontend job. The initial frontend attempt failed five World-mode Playwright tests; the rerun succeeded.
- Added regression tests only for malformed CI-status JSON/contracts, transport failure, and missing tenant-to-repository mapping. No production provider behavior changed.
- **Evidence boundary:** CI/test evidence only. Live GitHub mutation, production credentials/configuration, deployment, rollback, and production readiness remain unverified. Metrics unchanged: actionable 77%; full-scope 46%; A0/A1/A2/A3/A4 = 100/30/100/0/0.
- **Next:** supervised, explicitly authorized external validation of the supported `git_branch` operation in a disposable test repository/branch, with configured credentials and a cleanup plan.


## 2026-10-15 continuation — PR #1168

- **Merged:** PR #1168; merge commit `9f64f8f78b9e828911629bce4ea2230c7015042f`.
- **Exact tested head:** `79c28b1e5926ea2379846ddc6d3a413cd898cf4f`; all 17 check runs succeeded.
- The branch-create provider now requires exact `refs/heads/{branch_name}` response identity as well as a valid matching source SHA. A regression test covers a wrong ref with a matching SHA; the response is not treated as success and goes through the existing single read-only reconciliation, with no POST retry.
- **Evidence boundary:** CI and mocked tests only. Live GitHub mutation, operator credentials/configuration, deployment, rollback, and production readiness remain unverified. Progress metrics unchanged: actionable 77%; full-scope 46%; A0/A1/A2/A3/A4 = 100/30/100/0/0.
- **Next:** supervised, explicitly authorized external validation of `git_branch` in a disposable test repository/branch, with verified tenant/repository/token configuration and a cleanup plan.


---

## Acceptance update ? 2026-10-22 (local evidence; no release certification)

### Customer support / Issue #1043

- Verified from detached `main` source SHA `19ddcc072dc386ccce17baa858c0c2fb94db5171` using an isolated verification API container and dedicated `support_test` PostgreSQL database. Existing local application stacks and production were not targeted.
- Browser-to-real-API customer workflow passed: create ticket, submit reply, reload page, and confirm ticket/reply persistence.
- Attachment acceptance passed through the browser UI: upload a synthetic 61-byte text file with a reply, reload and confirm attachment metadata persisted, download through the application's authorized endpoint, and compare downloaded bytes exactly against the original (61/61 bytes matched).
- Customer access to the reseller-only API returned HTTP 403 in the real-API authorization check. This is separate from mocked Playwright route-guard tests.
- `backend/tests/test_support_escalation_postgres_api.py`: 1 passed against isolated `support_test`; `tests/test_world_support_inbox.py` and `tests/test_world_support_messages.py`: 24 passed; `git diff --check`: passed.
- The first attachment attempt was denied because the synthetic test account lacked `file.write`; assigning its role through the application's role-assignment service corrected the test fixture, after which the browser upload/reload/download flow passed. No support product code was changed for this acceptance run.
- The evidence was posted to [Issue #1043](https://github.com/ijoolaie/AI-Employee/issues/1043) in comment [#6332798320](https://github.com/ijoolaie/AI-Employee/issues/1043#issuecomment-6332798320). Keep the issue open for review and hand-off reconciliation; do not claim production certification.

### OpenTelemetry / SQLAlchemy dependency compatibility

- In the isolated verification worktree only, `backend/requirements.txt` and `backend/pyproject.toml` now constrain `sqlalchemy[asyncio]` to `>=2.0.36,<2.1.0`, aligning declared dependencies with the installed OpenTelemetry SQLAlchemy instrumentation's upper bound. The existing lockfile pin at SQLAlchemy 2.0.36 remains in range.
- Rebuilt isolated API reported SQLAlchemy 2.0.55; `pip check` passed; the SQLAlchemy instrumentation listener was present; and an actual application-engine query against PostgreSQL returned `SELECT 1` successfully. Dependency/test validation passed; frontend unit tests reported 145 passed, and lint reported 0 errors with 5 pre-existing warnings.
- These dependency edits are submitted for code review separately from the support-acceptance evidence; no deployment or release is implied. Latest certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

### Workspace / cleanup boundary

- Browser auth files and the temporary API container/port `18022` and frontend dev server/port `13021` were removed/stopped. The dedicated isolated Compose verification stack remains on its own ports (`18021`, `13020`, `15433`, `16390`); pre-existing application stacks were not stopped.
- Synthetic acceptance records remain in the dedicated `support_test` database; no broad database cleanup was performed.
- No deployment, release, or production-certification action was performed.

---

## MVP Phase 1 checkpoint — 2026-10-22 (isolated local acceptance; no release certification)

### Repository and runtime audit

- Exact source checkout used for this verification: `471d6457d6cf5f996f0059b2083387b2682db64e` (`main` at the time of the audit). The checkout used for the documentation change was created from this exact SHA.
- The current open-PR search returned no open PRs. Dependabot PR #1239 is closed unmerged; its focused replacement #1241 merged, followed by PR #1245. The 2026-10-21 handoff note that #1239 was still open is historical.
- Verification used only the isolated local stack: frontend `127.0.0.1:13020`, API `127.0.0.1:18021`, PostgreSQL `127.0.0.1:15433`, and Redis `127.0.0.1:16390`. The primary local worktrees and their pre-existing untracked files were left untouched.
- The first Run stayed `pending` because the isolated stack had no execution worker, outbox worker, Beat scheduler, or control worker running. Starting the required services enabled the outbox dispatch and execution tasks. This was a local runtime activation/configuration gap; no application source fix was made for it.
- The isolated API and execution worker were temporarily configured through an untracked `%TEMP%` Compose override to use the actual local LM Studio provider. The same temporary override set `GIT_COMMIT_SHA` to the verified source SHA; `/health` then returned the matching SHA. This was local test configuration only, not a tracked Compose or production change.

### Acceptance evidence

- Real-stack auth API passed: register, login, current-user read, refresh, and current-user read after refresh, using synthetic test identities.
- Employee/Run acceptance passed with the deterministic certification provider: tenant/license fixture, Employee creation and version publication, list/detail reads, Run creation, terminal success, and result validation.
- Actual local-model acceptance passed with LM Studio `google/gemma-4-e4b`. The worker logged HTTP 200 for `/v1/chat/completions`; the Run completed successfully in about 19.8 seconds and returned `LIVE_MODEL_EXECUTION_OK.`. A separate authenticated read returned the same persisted output.
- Browser acceptance passed on the isolated frontend: login, Run detail rendering, and full browser reload with the model output still visible. The one generic console 404 was traced to `http://127.0.0.1:13020/favicon.ico`; it was not an API or Run-result failure and remains a small UI polish item.

### Evidence boundary and next step

- This is synthetic, local engineering evidence. It is not a real-customer pilot, willingness-to-pay evidence, production deployment, or release certification.
- The certified production release remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`. No release or deployment occurred as part of this checkpoint.
- The next product decision remains evidence-based: compare the store customer-support journey with the Employee Run workflow against a specific customer segment and measurable pain, then seek genuine trial/payment intent. Do not expand employee roles or broad integrations before that decision.

---

## Report Employee real-model acceptance — 2026-10-22

This run validates the narrow report-analysis workflow against current `main` source SHA `ccf3a253d817b4be37e0f51fea89cd5524ce7aa9` in the isolated local verification stack. API `/health` reported the same SHA. The API and execution worker used a temporary, untracked Compose override for local LM Studio `google/gemma-4-e4b`; no production or primary local stack configuration was changed.

### Test fixture and result

- Seeded the system `report-employee`, registered a synthetic tenant, and issued a synthetic test license with `employee.run` and `tool:analyze_dataset`.
- Uploaded synthetic `report-analyst-test.csv` (source file ID `e6bd4310-1fb6-4c79-a742-d8a6037bfc9a`) containing three rows: Book A / A- / 10 units / 120 unit price; Book B / A- / 5 / 200; Book C / A- / 8 / 75.
- Run ID: `ec3c500f-4f18-4dfd-bc2f-2d082db5bc42`. Final status `success`; 2,536 tokens; execution task completed in about 99.7 seconds. Both LM Studio chat-completion requests returned HTTP 200.
- The generated analysis returned the correct calculations: 23 units; total revenue $2,800; Book A $1,200, Book B $1,000, Book C $600; average unit price about $131.67. A separate authenticated Run read returned the same persisted output.
- Generated report artifacts were present in the Run output: PDF ID `e82678a2-cf18-4e94-9fb2-ff1efb4e479c`, Excel ID `efd5662a-a8ca-4e45-a41b-0da325702ec1`, and three chart IDs. Authenticated downloads passed: PDF 65,658 bytes with `%PDF` signature, Excel 5,576 bytes with ZIP/OOXML signature, and Chart 1 PNG 24,448 bytes with PNG signature.
- Browser login, Run detail rendering, and full browser reload passed. The report KPI text remained visible after reload; the PDF, Excel, and Chart 1 buttons each completed a browser download.
- Worker logs show the Run task succeeded. The PostgreSQL active lock-wait count was zero after completion, with no deadlock or lock-timeout markers for this execution.

### Interpretation

This is meaningful local engineering evidence that the Report Employee can use a real local model, analyze uploaded data, persist its result, and produce downloadable artifacts. The CSV, account, tenant, and license were synthetic. It is not evidence of real-customer demand or willingness to pay, and it does not certify production or a new release. Production certification remains `v1.4.17` at `b403c0dcdea579e017738a6fdea138c2b1a2999c`.