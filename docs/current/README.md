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

## Current release position

- Published release: **`v1.4.1`**.
- Release SHA: **`f7f5062feb125c7ca50263f74a0e40bc4abfa591`**.
- Exact-SHA Production Certification: **SUCCESS**, run `34696339261`.
- External production deployment: **NOT VERIFIED**.
- Live provider validation and customer acceptance: **PENDING**.

## Current engineering position

- Phase 11: complete.
- Phase 12: operationally hardened.
- Phase 13: engineering complete.
- Phase 14.1–14.16: engineering complete where tracked.
- Stage 7: external production execution/certification pending.
- Stage 8: governed Agent workforce engineering active.

## Active Agent capability phases

1. Tool Calling contract and E2E.
2. Structured Arguments / JSON Schema fail-closed validation.
3. Multi-step execution with bounded loops.
4. Real-provider validation, starting with LM Studio.
5. Exact-SHA release gate for any promoted code.

## Infrastructure baseline

Recommended initial production target: **8 vCPU / 16 GB RAM / 150–200 GB NVMe/SSD / Ubuntu 24.04 LTS**, with fixed/public IP, TLS ingress, hardened firewall, encrypted off-host backups and centralized observability.

See `PRODUCTION_SERVER_BASELINE.md` for staging and growth tiers, topology, secrets, backup/restore and evidence requirements.

## Rule

Do not create another status, roadmap or release-truth document when an existing canonical document can be updated. Current documents must distinguish engineering evidence from real external production evidence.
