# Portfolio Master Status

> Canonical cross-project status register. Reconcile against live GitHub before acting; this file is a snapshot, not a substitute for current PR/Issue/CI checks.
>
> **Last reconciled:** 2026-11-01  
> **Maintainer:** ijoolaie

## Portfolio overview

| Project | Repository / tracking | Main status | Open PRs | Open issues | Latest inspected main SHA |
|---|---|---|---:|---:|---|
| AI-Employee | [ijoolaie/AI-Employee](https://github.com/ijoolaie/AI-Employee) | Active; commercial portal PR blocked by frontend Playwright regression | 3 | 9 | `a781c5941c8449483fa521149e792a84877efcb0` |
| Nova-Audit | [ijoolaie/Nova-Audit](https://github.com/ijoolaie/Nova-Audit) | Build/integrity repaired; Cloudflare 1101 diagnosis awaits runtime evidence | 0 | 0 | `4d4c92f074924c027c0dc2345d20a104a9752e57` |
| IranPriceScout | [ijoolaie/IranPriceScout](https://github.com/ijoolaie/IranPriceScout) | Worker deployed at PR #19; PR #20 merged but not deployed | 0 | 0 | `687edf82feca527ce12d91735373417419a72f04` |
| imoxy-net | [ijoolaie/imoxy-net](https://github.com/ijoolaie/imoxy-net) | Implementation progressing; D1/data-plane and reference-parity gates remain | 0 | 1 | `abc38a1392cc57a2ad7b3ca388d4a42820a232bb` |
| Raya MCP | Local workspace identified: `C:\\Users\\Ali\\local-mcp-bridge`; GitHub repository not created | Local MCP project; repository creation/upload blocked because the local MCP server is currently not initialized, so files and Git state cannot yet be inspected | N/A | N/A | Local SHA not verified |

**Totals for the four accessible repositories at this snapshot:** 3 open PRs (including this portfolio-register PR) and 10 open issues. Raya MCP is excluded until its canonical repository is identified.

## 1. AI-Employee

- **Repository:** https://github.com/ijoolaie/AI-Employee
- **Default branch / inspected HEAD:** `main` / `a781c5941c8449483fa521149e792a84877efcb0`
- **Latest production-certified release recorded in handoff:** `v1.4.17`, SHA `b403c0dcdea579e017738a6fdea138c2b1a2999c`.

### Open PRs

| PR | Status | Disposition |
|---|---|---|
| [#1334 — commercial portal license management and tenant access boundaries](https://github.com/ijoolaie/AI-Employee/pull/1334) | Open, not draft | Do not merge yet. Exact-head workflow inventory: 16 runs completed; 15 succeeded and the CI workflow failed in frontend Playwright browser regressions. Backend job passed. |
| [#1257 — World close-up zoom](https://github.com/ijoolaie/AI-Employee/pull/1257) | Open, Draft | On hold pending authenticated real-runtime desktop/mobile evidence and human visual approval. |
| [#1335 — portfolio master status register](https://github.com/ijoolaie/AI-Employee/pull/1335) | Open, documentation-only | This register. Created on a dedicated branch because main requires PR review and two status checks; exact-head workflow runs had not appeared at last inspection. Do not merge until required checks pass. |

Failing CI: [run 41297949329](https://github.com/ijoolaie/AI-Employee/actions/runs/41297949329). Backend passed; frontend failed at **Playwright browser regressions**. The other 15 workflow runs in the inspected exact-head inventory succeeded. Local validation in the PR body does not override the failed GitHub browser regression.

### Open issues

- [#1258](https://github.com/ijoolaie/AI-Employee/issues/1258) — multi-turn customer-support acceptance; active engineering/customer acceptance tracker.
- [#1288](https://github.com/ijoolaie/AI-Employee/issues/1288) — durable staff notification and acknowledgement; external SMTP/inbox delivery, named owner, assignment and measurable SLA remain unproven.
- [#1044](https://github.com/ijoolaie/AI-Employee/issues/1044) — World visual/gameplay specification; deferred with PR #1257.
- [#1061](https://github.com/ijoolaie/AI-Employee/issues/1061) — validate a revenue-generating workflow; commercial discovery gate. Handoff target: five decision-maker conversations and at least two concrete sample/trial commitments.
- [#1305](https://github.com/ijoolaie/AI-Employee/issues/1305) — tenant-safe retention/purge; logical expiry exists, physical purge is gated on owner approval of retention duration, audit requirements and schedule.
- [#19](https://github.com/ijoolaie/AI-Employee/issues/19) — production evidence for Vendor/Reseller/Customer isolation and RBAC.
- [#210](https://github.com/ijoolaie/AI-Employee/issues/210) — immutable external-production release promotion.
- [#259](https://github.com/ijoolaie/AI-Employee/issues/259) — scale, governance and production master plan.
- [#269](https://github.com/ijoolaie/AI-Employee/issues/269) — external production certification and customer acceptance.

### Verified progress

- PRs #1330, #1331 and #1332 are merged; the handoff records exact-head CI results of 12/12, 9/9 and 16/16 respectively.
- Customer-support acceptance records 136 passing tests across 18 files, including PostgreSQL-backed handoff, acknowledgement/follow-up, tenant-isolated escalation, outbox, dispatcher, email-worker and multi-turn persistence.
- Browser acceptance covers widget/API/Run/worker response persistence with a deterministic test provider. It does **not** establish live LLM quality or customer satisfaction.
- Handoff notification was exercised through the real application worker to a localhost-only Mailpit sink. This is not external SMTP delivery or proof of staff response.
- Shopify pagination hardening is merged; incomplete pagination must fail rather than silently mark a partial sync complete.
- Unknown Shopify inventory is represented separately from provider-confirmed zero; no live Shopify sync is claimed.
- Mainline CI and merged work do not certify a production release or deployment.

### Next actions

1. Inspect PR #1334's failing Playwright output, reproduce the browser regressions and repair the underlying issue without weakening assertions.
2. Re-run exact PR-head CI; require all mandatory checks to pass before merge.
3. Keep #1257 on hold until real-runtime screenshots and human approval exist.
4. Continue #1258/#1288 acceptance without treating deterministic tests or Mailpit as production evidence.
5. Prioritize #1061 customer discovery before broadening integrations.
6. Do not enable physical purge under #1305 before explicit policy-owner approval.
7. Keep external production/release gates #19, #210, #259 and #269 separate from CI.

## 2. Nova-Audit

- **Repository:** https://github.com/ijoolaie/Nova-Audit
- **Inspected HEAD:** `4d4c92f074924c027c0dc2345d20a104a9752e57`
- **Handoff:** [HANDOFF.md](https://github.com/ijoolaie/Nova-Audit/blob/main/HANDOFF.md), updated 2026-10-20.
- **GitHub inventory:** no open PRs and no open issues. PR #2 build/lockfile verification fix is merged; PR #3 refreshed the handoff.

### Verified progress recorded in handoff

- Clean-clone `npm ci`, `npm run build`, `node --check worker.js`, `npm test` (4 tests), `npm run check`, and `npm audit --audit-level=high` passed.
- Release Worker SHA-256 matched the checksum manifest.
- Windows line-ending conversion was addressed with `.gitattributes`.
- No deployment was performed as part of the build/integrity repair.

### Blocker

Cloudflare Error 1101 remains undiagnosed. The Worker name `web-app` in repository config was not found in the currently selected Cloudflare account (error 10007). This does not prove that no deployed Worker exists. Actual Worker name/URL/account and runtime exception remain unknown.

### Next actions

1. Identify the correct Cloudflare account, actual Worker name and URL from the dashboard.
2. Capture read-only runtime logs/stack trace while reproducing 1101; redact secrets and customer data.
3. Fix only a demonstrated cause, add a regression test and validate in an isolated Worker first.
4. Require explicit approval before production deployment or changes to production bindings/secrets.

**Status:** repository repair complete; original runtime-diagnosis objective blocked on external runtime identity/log evidence.

## 3. IranPriceScout

- **Repository:** https://github.com/ijoolaie/IranPriceScout
- **Inspected HEAD:** `687edf82feca527ce12d91735373417419a72f04`
- **Handoff:** [docs/HANDOFF.md](https://github.com/ijoolaie/IranPriceScout/blob/main/docs/HANDOFF.md), updated 2026-10-31.
- **GitHub inventory:** no open PRs and no open issues.
- PR #19 (Serper result-limit fix) is merged and was deployed.
- PR #20 (explicit search redirect URL normalization) is merged but **not deployed** according to the latest handoff.

### Production evidence and limitations

- Handoff records a Cloudflare Worker deployment after PR #19 with 100% traffic on the deployed version.
- GET-only health checks returned HTTP 200.
- A user-initiated search after that deployment completed the Serper-backed web run without the previous HTTP 400; handoff records 39 raw results and 28 eligible results.
- PR #20 unwraps only explicit absolute HTTP(S) destinations in known Google/Bing/Yahoo query parameters. It does not follow arbitrary redirects or decode opaque tokens.
- Observed Google `/goto?url=CAES...` values remain opaque; investigation found binary/protobuf-like payload, not a directly extractable URL.
- PR #20 was not deployed at the latest handoff checkpoint. Do not imply that the deployed Worker includes it.
- Torob has previously returned an upstream blocked/challenged condition; Telegram is not configured; Instagram data is limited to publicly indexed results.
- Parsed prices are heuristic and must not be described as seller-confirmed live prices.

### Next actions

1. Review PR #20 and decide whether the opaque Google URL limitation is accepted or needs a narrowly scoped resolver.
2. Do not use arbitrary redirect following or unrestricted destination fetching; preserve SSRF/DNS/IP and retailer-host protections.
3. Prepare a clean isolated release checkout, run the full test suite and Wrangler dry-run, and deploy only after exact merged code is verified.
4. After deployment, ask the user to initiate the next real scan from the UI. Management tools must not call `/api/scan` or trigger ingestion.
5. Validate price extraction and outliers using fixtures first; distinguish parsed offers from verified retail prices.

**Status:** deployed MVP at the PR #19 baseline; PR #20 is merged but awaiting safe release/deployment and further validation.

## 4. imoxy-net

- **Repository:** https://github.com/ijoolaie/imoxy-net
- **Inspected HEAD:** `abc38a1392cc57a2ad7b3ca388d4a42820a232bb`
- **Handoff:** [HANDOFF.md](https://github.com/ijoolaie/imoxy-net/blob/main/HANDOFF.md)
- **GitHub inventory:** no open PRs; one open issue: [#78 — prove bounded downstream WebSocket buffering in Cloudflare Workers](https://github.com/ijoolaie/imoxy-net/issues/78).
- Latest inspected commit is a handoff update recording quota-recovery work in PR #150.

### Product scope and implementation

Target is behaviorally compatible implementation against pinned Nova Proxy 5.0.0, followed by separately approved improvements. Interfaces: web panel, Telegram bot and Android APK, sharing API/domain and authorization/quota logic.

Handoff records foundations including:
- Worker API authentication/session, account CRUD foundations, quota/usage foundations and subscription lifecycle.
- Web login/session, account list/create, usage summary and read-only Cloudflare inventory/preview.
- Telegram allowlisted private-chat read-only commands, update-ID deduplication, stale-claim recovery and cleanup.
- Android HTTPS login/account list/refresh/logout with Android Keystore-backed session storage.
- Quota overflow guard and recovery improvements.

### Acceptance gaps

- Cloudflare operations remain read-only inventory and dry-run planning; no apply/delete/write route is enabled.
- SQLite tests are not a substitute for real Cloudflare D1 validation.
- Real D1 migration, backup/restore, concurrency and failure-injection tests remain.
- Full browser E2E/accessibility, Android device/emulator E2E, secure Telegram account linking and real webhook validation remain.
- Nova reference runtime parity has not been proven. Handoff requires an authorized disposable Nova Proxy 5.0.0 instance and qualified license/distribution review.
- Issue #78 remains the immediate WebSocket bounded-buffer acceptance gate.
- No production deployment, real Cloudflare write, live Telegram API call or Nova runtime comparison is claimed.

### Roadmap phases explicitly reported by handoff

| Phase | Status | Evidence / exit gate |
|---|---|---|
| 0–10 | Needs reconciliation | Current handoff summary does not provide a complete per-phase 0–10 status table; do not infer completion. |
| 11 | In progress | Initial API/Telegram account-list contract tests pass; full cross-interface E2E, failure injection, SLOs and mutation parity remain. |
| 12 | Blocked | Legal/distribution approval, reference runtime evidence, real D1 backup/restore, staging deployment and production release artifact absent. |
| 13 | Not started | Candidate improvements documented; gated on parity and legal review. |

### Next actions

1. Continue issue #78 with bounded-buffer proof and safe failure-injection tests.
2. Obtain an authorized disposable reference instance and qualified license/distribution review before claiming parity.
3. Add real D1 migration/backup/restore/concurrency validation.
4. Add web/Android E2E and secure Telegram account linking in a safe test environment.
5. Keep Cloudflare writes disabled until least privilege, preview approval, idempotency and rollback are demonstrated.
6. Do not start Phase 13 before parity and legal gates pass.

## 5. Raya MCP — local project, GitHub onboarding pending

- **Known local workspace:** `C:\\Users\\Ali\\local-mcp-bridge` (listed among Raya MCP's configured workspace roots).
- **GitHub repository:** not yet created; no canonical remote was found in the connected GitHub repository searches.
- **Local audit status:** blocked. The first workspace-root listing succeeded, but subsequent local filesystem/Git requests returned `MCP server is not initialized`. Therefore the directory contents, current Git branch, uncommitted changes, existing remote, tests, secrets exposure and local commit history have not been verified.
- **Planned GitHub visibility:** Private, as the project controls local filesystem and system capabilities. Do not publish it publicly by default.
- **Important:** Do not upload the directory wholesale. First inspect and exclude `.env*`, credentials, tokens, certificates, private keys, local databases, logs, caches, build artifacts, user data, and any machine-specific configuration. Review the proposed file list before the first push.
- **Known historical context only:** prior conversations described a 45-tool inventory, but that is not proof that all 45 tools currently exist in the local source or are operational. Re-audit source, tests and runtime independently.

### Onboarding sequence

1. Restore/initialize the local Raya MCP connection and inspect `C:\\Users\\Ali\\local-mcp-bridge` read-only.
2. Determine whether it is already a Git repository; inspect remotes, branch, commit history, working-tree changes and ignored/untracked files. Preserve all user changes.
3. Review project structure, README, package manifests, tests, roadmap, handoff, agent/rules files and tool registration.
4. Prepare a reviewed `.gitignore` and secret-safe initial file manifest; do not delete or overwrite local files.
5. Create a **private** GitHub repository under the user's account, then add the remote and push only the reviewed source/history. If the GitHub connector cannot create repositories, use the authenticated GitHub UI/CLI after local access is restored.
6. Verify the remote SHA, default branch, pushed file list and CI; add the canonical repository URL to this portfolio register.
7. Audit PRs, Issues, Roadmap, Handoff and the 45-tool inventory against the uploaded source and runtime evidence.

**Current status:** project identified locally; not yet inspected, not uploaded, and no GitHub repository has been created.

## Portfolio operating rules

1. Before every project action, refresh the default-branch SHA, open PRs, open issues and relevant workflow runs. This file can become stale.
2. PR merge readiness requires exact-head required checks to pass, review threads to be resolved, and base/head freshness to be checked. Green CI alone is not production certification.
3. Never count documentation-only progress as functional implementation progress.
4. Never claim a feature works solely because it appears in README, roadmap or handoff. Require source inspection and relevant tests/runtime evidence.
5. Keep GitHub evidence separate from local machine, Docker, Cloudflare, provider, customer and production evidence.
6. Record blocked work with the missing evidence/external dependency and a concrete next action.
7. Do not deploy, change production resources, trigger customer scans/ingestion, read secrets or perform destructive actions unless the user authorized that exact operation.
8. Update this file only after reconciling the affected project against live GitHub and relevant handoff/roadmap.
9. Percent-complete values are intentionally omitted until each project's roadmap phases and exit criteria are mapped to verifiable evidence. Do not invent progress percentages.

## Next portfolio maintenance cycle

1. Add the canonical Raya MCP repository once identified, then audit its PRs, issues, roadmap, handoff and runtime/tool evidence.
2. Resolve AI-Employee PR #1334's Playwright failure; keep #1257 on hold.
3. Decide and execute the safe isolated deployment path for IranPriceScout PR #20.
4. Obtain the actual Nova-Audit Cloudflare Worker identity and runtime logs.
5. Continue imoxy-net issue #78 and D1/reference-parity acceptance.
6. Reconcile this file after each material merge, release, deployment or acceptance milestone.
