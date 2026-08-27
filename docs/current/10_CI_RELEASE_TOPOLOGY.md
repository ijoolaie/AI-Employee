# CI / Release Topology

**Status date:** 2026-08-27
**Current certified vendor release:** `v1.2.0`
**Current implementation baseline:** `V1.4`
**Current external-production gate:** `Phase 6E — pending real target execution`

> Release truth is defined by `docs/current/39_RELEASE_TRUTH_V1.2.0.md`. Historical release documents must not be treated as the current release state.

## Purpose

This document defines the boundary between normal development CI, production-like certification, deployment/recovery evidence, and release execution.

> Fast CI proves that a change is safe to merge. Production Certification proves that a release candidate works on the production-like stack. Release execution publishes only a revision that has already passed the applicable gates.

## 1. Gate layers

| Layer | Primary responsibility | When it should run | Release decision |
|---|---|---|---|
| PR / fast CI | lint, unit, contract, build, architecture | pull requests and normal development | merge safety |
| Integration / Compose validation | PostgreSQL/Redis/Compose compatibility | change-triggered or explicit validation | runtime compatibility |
| Product Acceptance | executable real-stack product flows | explicit acceptance/certification runs | capability evidence |
| Production Hardening | security, recovery, persistence, operational contracts | explicit hardening runs | certification evidence |
| Production Certification | complete production-like stack + product gates | release tag or manual dispatch | release gate |
| Deployment / DR / Rollback | deployment and recovery behavior | deployment/recovery exercises | operational evidence |
| Release | tag, notes, artifacts, customer handoff | after applicable gates pass | publishable artifact |

## 2. Workflow ownership

- `architecture.yml` — architecture boundaries and completeness audit.
- `production-compose-validation.yml` — production-like Compose validation.
- `production-certification.yml` — release/manual production-like certification.
- `production-hardening.yml` — hardening/security/operational checks.
- `production-recovery-validation.yml` — backup/restore and recovery evidence.
- `production-dr.yml` — disaster-recovery evidence.
- `production-observability.yml` — observability and failure-detection contract.
- `production-notification-contract.yml` — notification contract.
- `production-notify.yml` — notification delivery/orchestration.
- `production-deploy.yml` — deployment orchestration.
- `production-deploy-target.yml` — target-specific deployment execution.
- `production-rollback.yml` — rollback execution.
- `release-artifact.yml` / delivery packaging workflows — immutable artifact generation.

## 3. Trigger policy

### Normal PR

Run the smallest set needed to answer:

- does the code compile?
- do tests and contracts pass?
- does architecture remain valid?
- does the frontend build?
- does changed infrastructure remain compatible?

A PR must not automatically launch the entire release-grade certification stack.

### Release tag

For `v*` tags:

1. verify immutable tag/revision identity;
2. run applicable production certification;
3. retain Actions evidence;
4. publish artifacts only after required gates pass.

### Manual certification

Use `workflow_dispatch` when release-grade evidence is needed without creating a new tag.

## 4. Failure triage rule

Triage red workflows in this order:

1. dependency/setup failure;
2. infrastructure failure;
3. shared application failure;
4. gate-specific failure;
5. release-only failure.

A lower-level failure must not be duplicated as an independent defect in downstream workflows.

## 5. Delivery topology

```text
Vendor / Primary Seller
        ↓
Reseller / Secondary Seller
        ↓
Customer / End Customer
```

Vendor owns platform release authority. Resellers and customers receive controlled, scoped delivery artifacts and administration boundaries.

## 6. Required release evidence

For a production release retain:

- immutable Git tag;
- exact commit SHA;
- release notes;
- Production Certification evidence;
- applicable Product Acceptance evidence;
- applicable Hardening/DR/Recovery evidence;
- deployment-tested revision;
- rollback evidence when performed;
- reseller/customer handoff manifest.

Never include credentials, private keys, production endpoints, or provider secrets in release artifacts.

## 7. Current roadmap alignment

The repository has three distinct truths:

1. **Product release truth:** `v1.2.0` is the latest certified controlled vendor release.
2. **Implementation truth:** `V1.4` is the active architecture/implementation baseline.
3. **External-production truth:** Phase 6E remains pending until a real target is available and the target-specific evidence exists.

Therefore new implementation work must not silently relabel V1.4 as a released external-production version.

## 8. Definition of done

- every workflow has one primary responsibility;
- release-grade certification is not duplicated as default PR CI;
- release tags invoke the required release-grade gates;
- failures are classified by layer;
- release evidence maps to one immutable revision;
- Vendor/Reseller/Customer boundaries are represented;
- release truth and implementation baseline remain explicitly separated.
