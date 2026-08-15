# Package Changelog v1.10

## v0.2.47 — Phase 1 Developer Console

- Added tenant-scoped Developer Console at `/developer`.
- Added read-only audit-log inspection through `/api/v1/operations/audit-logs`.
- Added operational metrics, recent runs, trace links and dead-letter replay controls to the Developer Console.
- Added focused Developer Console contract coverage.
- Added `documents/57_PHASE_1_DEVELOPER_CONSOLE_AS_BUILT_v0.2.47.md`.
- Updated backend (`pyproject.toml` + `main.py`) and frontend package versions to 0.2.47.
- Preserved the complete cumulative project package; no real `.env`, credentials, cache or bytecode artifacts are shipped.
