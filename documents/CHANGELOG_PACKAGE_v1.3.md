# AI Employee Platform — Documentation Package Changelog

## v1.3 — 2026-08-06

### Summary

Frontend Customer Panel MVP (frontend v0.1.0) implemented against backend v0.2.0. Documentation updated to reflect as-built status.

### Changes

| Document | Change |
|----------|--------|
| **08_Frontend** | Bumped to **v1.2**. As-built structure, tech stack versions, implemented pages (Dashboard / Employees / Runs / Files / Settings), API mapping, auth flow, and deferred items recorded. |
| **CHANGELOG_PACKAGE** | This file (v1.3). |

### Companion deliverable

- **frontend_v0_1_0.zip** — Next.js 15 Customer Panel source (see `frontend/README.md`).

### Files unchanged

All other documents remain at their previous package versions:
00 Master Plan, 01 Product Vision, 02 Business Model, 03 Roadmap (v1.1),
04 Architecture, 05 Database, 06 API, 07 Backend, 09 UI/UX,
10 AI Core (v1.1), 11 Employee Framework, 12 Workflow Engine,
13 Integrations, 14 Security, 15 Deployment, 16 Testing, 17 Marketing,
18 Sales, 19 Finance, 20 Changelog, 21 CrossCutting Additions.

### Next recommended steps

1. Run frontend against live backend; harden auth edge cases and error surfaces.
2. Add minimal Admin shell (tenants list) if needed for internal ops.
3. Fold Cost Dashboard UI once AI Gateway cost data is queried in aggregate (Phase 2).
4. Merge accepted items from `21_CrossCutting_Additions` into Architecture / Security / Backend body docs in a future v1.4 content revision.

---

*End of package changelog v1.3*

> **Current-state synchronization (v0.2.9-LMSTUDIO, 2026-08-07):** This document remains authoritative for its planned/design scope. Current implementation status is tracked in `00_AS_BUILT_BASELINE_v0.2.9_LMSTUDIO.md` and `23_AS_BUILT_CURRENT_STATE_v0.2.9.md`. LM Studio is the default local provider; Windows Celery uses `--pool=solo`; the real `.env` is excluded from release packages.

