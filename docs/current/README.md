# Current Documentation

This directory contains maintained documentation for the current `main` implementation line. Release certification is separate from current-main validation and external production/customer acceptance.

## Source of truth

1. `CAPABILITY_REALITY_AUDIT_AND_COMMERCIAL_READINESS_PLAN_2026-10-13.md` — documentation-drift root cause, role-by-role capability audit, commercial gates and acceptance sequence.

2. `../00_START_HERE/VERSIONING_TRUTH.md` — release/architecture/phase truth.
3. `../00_START_HERE/CURRENT_STATUS.md` — executive current state.
4. `../00_START_HERE/CURRENT_PRIORITIES.md` — immediate execution order.
5. `PRODUCTIZATION_ROADMAP.md` — delivery roadmap and current Agent capability phases.
6. `PRODUCTION_SERVER_BASELINE.md` — recommended external production infrastructure baseline.
7. `PRODUCTION_EVIDENCE_INDEX.md` — external evidence boundary.
8. `PRODUCTION_CERTIFICATION_EXECUTION_PACK.md` — exact-SHA certification procedure.
9. `EXTERNAL_PRODUCTION_EXECUTION_PACK_2026-09-26.md` — operator-facing execution sequence for remaining external production gates.

## Current release position

- Latest published/certified release: **`v1.4.17`**.
- Exact certified SHA: **`b403c0dcdea579e017738a6fdea138c2b1a2999c`**.
- Production Certification run: **`37625345534`**; job **`112805570856`**.
- External production deployment: **NOT VERIFIED / NOT CLAIMED**.
- Live provider validation, deployed-target security evidence, customer acceptance and realized external revenue: **NOT VERIFIED / PENDING EXTERNAL EXECUTION**.
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