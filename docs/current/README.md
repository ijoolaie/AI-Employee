# Current Documentation

This directory contains maintained documentation for the current `main` implementation line.

## Source of truth

1. `../00_START_HERE/VERSIONING_TRUTH.md` — release/architecture/phase truth.
2. `../00_START_HERE/CURRENT_STATUS.md` — executive current state.
3. `../00_START_HERE/CURRENT_PRIORITIES.md` — immediate execution order.
4. `PRODUCTIZATION_ROADMAP.md` — delivery roadmap and current Agent capability phases.
5. `PRODUCTION_SERVER_BASELINE.md` — recommended external production infrastructure baseline.
6. `PRODUCTION_EVIDENCE_INDEX.md` — external evidence boundary.
7. `PRODUCTION_CERTIFICATION_EXECUTION_PACK.md` — exact-SHA certification procedure.
8. `EXTERNAL_PRODUCTION_EXECUTION_PACK_2026-09-26.md` — operator-facing execution sequence for remaining external production gates.

## Current release position

- Latest published/certified release: **`v1.4.11`**.
- Exact certified SHA: **`90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`**.
- Production Certification run: **`35848311037`**; job **`107139710452`**.
- External production deployment: **PENDING**.
- Live provider validation, deployed-target security evidence and customer acceptance: **PENDING EXTERNAL EXECUTION**.
- Current `main` is post-certification engineering/documentation work and is not represented as an exact-SHA certified release.

## Current engineering position

- Phase 11: complete.
- Phase 12: operationally hardened.
- Phase 13: engineering complete.
- Phase 14 engineering gates tracked by the current status/evidence documents.
- External production execution/certification remains pending.
- Governed Agent/workforce semantic engineering remains active.

## Infrastructure baseline

Recommended initial production target: **8 vCPU / 16 GB RAM / 150–200 GB NVMe/SSD / Ubuntu 24.04 LTS**, with fixed/public IP, TLS ingress, hardened firewall, encrypted off-host backups and centralized observability.

See `PRODUCTION_SERVER_BASELINE.md` for staging and growth tiers, topology, secrets, backup/restore and evidence requirements.

## External production execution

Use `EXTERNAL_PRODUCTION_EXECUTION_PACK_2026-09-26.md` when a real production target is available. It separates engineering/rehearsal evidence from target evidence and defines the required gate order, PASS/FAIL criteria and final evidence handoff.

## Rule

Do not create another status, roadmap or release-truth document when an existing canonical document can be updated. Current documents must distinguish engineering evidence from real external production evidence.