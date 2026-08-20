# AI Employee Platform — Current Roadmap

**Updated:** 2026-08-20  
**Current baseline:** `27dc0aa` (local release verification branch)  
**Repository baseline:** RC8 / release-candidate lineage

## Current position

The project is **not at the beginning of implementation**. The implementation roadmap is substantially complete and the project is currently in the **Release / final handoff phase**.

The roadmap must not send a new run through dependency installation, requirements setup, CI certification, release-evidence generation, or production certification when those gates already have accepted evidence.

## Completed gates

| Gate | Status | Current evidence |
|---|---|---|
| Core product implementation | ✅ Complete | Existing repository modules, workflows and historical release evidence |
| CI certification | ✅ Complete | Existing repository workflow/evidence set |
| Release evidence / artifacts | ✅ Complete | Existing release evidence and artifact records |
| Final production certification | ✅ Complete | Existing certification evidence plus local production verification |
| Local production Compose validation | ✅ Complete | `docker compose ... config --quiet` PASS |
| Local production build | ✅ Complete | API/worker/beat/frontend images built successfully |
| Local production deployment | ✅ Complete | API, frontend, PostgreSQL, Redis, worker and beat running healthy |
| Runtime readiness | ✅ Complete | `/health/dependencies` returned `READINESS|PASS` and `LOCAL_PRODUCTION|readiness|PASS` |
| Rollback / recovery drill | ✅ Complete | Failure detection and API recovery both PASS |
| Working tree hygiene | ✅ Complete at verification point | `git status --short` returned clean |

## Important verification notes

- The first local production start exposed a real configuration mismatch: production CORS rejected `http://localhost:3000`. This was corrected in source/configuration before the successful deployment verification.
- The successful deployment showed all six runtime services healthy/running.
- The rollback drill intentionally stopped the API, detected the failure, restarted the known-good service, and verified dependency readiness after recovery.
- The shell script itself was not executed through WSL because Docker was unavailable in that WSL distro. The same drill was executed natively in PowerShell against Docker Desktop and passed. This is an environment limitation, not an application rollback failure.
- `/openapi.json` returning `404` is expected for this application because the API OpenAPI document is exposed at `/api/v1/openapi.json`; that endpoint returned `200`.

## What should NOT be repeated per run

The workflow/run process must not rebuild the environment unnecessarily.

**One-time / baseline setup:**
- install project dependencies;
- provision/start PostgreSQL and Redis;
- build container images when source/dependency inputs change;
- run migrations when migration inputs change;
- establish CI/release evidence.

**Per-run verification:**
- start/reuse the existing services;
- execute only the relevant application/workflow operation;
- inspect the resulting run, logs, health/readiness, and business outcome;
- reuse already-built images and installed dependencies unless inputs changed.

## Remaining roadmap: Release → Handoff

### R1 — Freeze release baseline
- [x] Freeze the verified source revision.
- [x] Record the verified runtime revision.
- [ ] Select/tag the final release commit according to the repository release policy.

### R2 — Release documentation synchronization
- [x] Update this roadmap.
- [x] Update the release audit from the old staging/NO-GO wording.
- [x] Update the master implementation guide so it describes the release phase rather than an implementation-first sequence.
- [ ] Add/confirm the final release tag and changelog entry.

### R3 — Final handoff
- [x] Local production deployment evidence captured.
- [x] Readiness evidence captured.
- [x] Rollback/recovery evidence captured.
- [ ] Attach the final release evidence/artifact bundle to the release record if not already attached.
- [ ] Perform the final human sign-off / release handoff.

### R4 — Post-release operations
- [ ] Monitor first production window.
- [ ] Triage only release-blocking regressions.
- [ ] Plan the next product increment separately from release certification.

## Definition of release-ready

Release-ready means:

1. Existing CI/release/certification evidence is accepted.
2. The target source revision is frozen.
3. Production configuration validates.
4. Runtime services start and remain healthy.
5. Application readiness passes.
6. A controlled failure is detected.
7. Recovery to the known-good service succeeds.
8. Release evidence is recorded and handed off.

At the current verification point, **items 1–7 are evidenced**. The only remaining roadmap work is release bookkeeping/handoff, not reimplementation or re-certification.
