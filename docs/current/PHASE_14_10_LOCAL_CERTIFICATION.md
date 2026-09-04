# Phase 14.10 — Local External-Production Certification Harness

Status: **IMPLEMENTED / EXTERNAL-PENDING**.

This harness makes the repository's local production-like checks executable as one reproducible evidence run. It pins the evidence to the exact checked-out Git SHA, records a Git archive checksum, starts the production-like Docker Compose stack, executes readiness and frontend checks, runs the backup/restore smoke, performs the recovery drill, and writes an evidence index.

## Run

From the repository root:

```bash
bash scripts/phase_14_10_local_certification.sh
```

The script expects the existing local production environment file (`.env.production`) and local Compose override. It uses the existing production-like deployment and recovery scripts rather than creating a second deployment substrate.

Optional controls:

```bash
CERTIFICATION_OUT_DIR=artifacts/certification-run \
COMPOSE_PROJECT_NAME=ai-employee-certification \
KEEP_STACK=false \
bash scripts/phase_14_10_local_certification.sh
```

A provider healthcheck can be supplied when a safe, non-secret URL is available:

```bash
PROVIDER_HEALTHCHECK_URL=https://example.invalid/health bash scripts/phase_14_10_local_certification.sh
```

The harness records only the HTTP status for that endpoint and never writes response bodies or authorization headers to the evidence directory.

## Evidence produced

The output directory contains:

- `identity.env` — exact Git SHA/ref, UTC timestamp and archive SHA256;
- `EVIDENCE_INDEX.md` — pass/fail matrix and explicit evidence boundary;
- command logs and status files for every executed gate;
- service snapshot and provider HTTP status when configured.

The generated evidence directory is intentionally an artifact, not source-of-truth documentation. Review it for secrets before sharing or retaining it outside the local machine.

## What this proves

A successful run is **local production-like engineering evidence** for the exact source SHA. It demonstrates that the checked-out candidate can be configured, deployed, health-checked, backed up/restored at smoke level, and recovered through the repository's local drill.

## What this does not prove

A successful local run does not by itself prove:

- independent deployment to the real external production target;
- live third-party provider certification;
- measured production SLO/error-budget attainment;
- target-infrastructure RPO/RTO;
- independent security/compliance attestation; or
- Vendor → Reseller → Client customer acceptance.

Those external records remain required by `PHASE_14_EXTERNAL_PRODUCTION_EVIDENCE.md` and the Phase 14.10 issue. Do not convert local PASS results into a production-certification claim.

## Three-environment execution model

For stronger local rehearsal, run the harness sequentially against three isolated configuration/tenant profiles (for example Platform, Reseller and Client) and preserve each run under a distinct evidence directory and Compose project. Do not reuse or cross-copy tenant data between profiles. Because the existing local Compose override reserves fixed host ports, the profiles should be run sequentially unless a dedicated port override is supplied.

## Acceptance disposition

The harness can support a later Phase 14.10 package, but the final disposition still must be **ACCEPTED**, **CONDITIONALLY ACCEPTED**, or **REJECTED / DEFERRED** based on the complete independent evidence package.
