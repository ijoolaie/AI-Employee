# CI / Release Topology

**Status date:** 2026-08-20
**Baseline:** `main` / release line `1.0.x`

## Purpose

This document is the authoritative boundary between normal development CI, production-like certification, deployment/recovery evidence, and release execution.

The rule is simple:

> Fast CI proves that a change is safe to merge. Production Certification proves that a release candidate works on the production-like stack. Release execution publishes only a revision that has already passed the applicable gates.

## 1. Gate layers

| Layer | Primary responsibility | When it should run | Release decision |
|---|---|---|---|
| PR / fast CI | lint, unit, contract, build, architecture | pull requests and normal development | required for merge where configured |
| Integration / Compose validation | real PostgreSQL/Redis/Compose compatibility | change-triggered or explicit validation | required when infrastructure/runtime changes |
| Product Acceptance | executable real-stack product flows | explicit acceptance/certification runs | required for a new product capability |
| Production Hardening | security, recovery, persistence, operational contracts | explicit hardening runs | required before production certification |
| Production Certification | complete production-like stack + product gates + Playwright | release tag or manual dispatch | release gate |
| Deployment / DR / Rollback | deployment and recovery behavior | deployment/recovery exercises | release evidence; not duplicate PR CI |
| Release | tag, notes, artifacts, customer handoff | after applicable gates pass | publishable artifact |

## 2. Workflow ownership

The repository currently has these workflow responsibilities:

- `architecture.yml` — architecture boundaries and completeness audit.
- `production-compose-validation.yml` — production-like Compose validation.
- `production-certification.yml` — final production-like certification. **This workflow is intentionally release/manual only.**
- `production-hardening.yml` — hardening/security/operational checks.
- `production-recovery-validation.yml` — backup/restore and recovery evidence.
- `production-dr.yml` — disaster-recovery evidence.
- `production-observability.yml` — observability and failure-detection contract.
- `production-notification-contract.yml` — notification contract.
- `production-notify.yml` — notification delivery/orchestration.
- `production-deploy.yml` — deployment orchestration.
- `production-deploy-target.yml` — target-specific deployment execution.
- `production-rollback.yml` — rollback execution.

## 3. Important anti-overlap rule

`production-certification.yml` is deliberately not a default `pull_request` or `main`-push workflow anymore.

It runs only for:

- `workflow_dispatch`
- version tags matching `v*`

This prevents the largest production-like test suite from becoming a second general-purpose PR CI pipeline. Its job still contains the complete certification sequence because it is the release-grade evidence source.

Do not copy those certification steps into other workflows unless a gate has a materially different purpose.

## 4. Trigger policy

### Normal PR

Run only the smallest set of workflows needed to answer:

- does the code compile?
- do unit/contract tests pass?
- does architecture remain valid?
- does the frontend build?
- does the changed infrastructure contract remain valid?

A PR should not automatically launch the entire production certification stack.

### Release tag

For `v*` tags:

1. verify the tag points at the intended immutable revision;
2. run Production Certification;
3. retain the resulting Actions run as release evidence;
4. publish release notes/assets only after the applicable release gate is green.

### Manual certification

Use `workflow_dispatch` when a release-grade certification run is needed without creating a new tag, for example after infrastructure-only changes or before a release candidate is frozen.

## 5. Failure triage rule

When several workflows are red, do not treat each red workflow as an independent product defect.

Triage in this order:

1. **Dependency/setup failure** — Python/Node/Docker/tooling/version mismatch.
2. **Infrastructure failure** — PostgreSQL/Redis/Compose readiness.
3. **Shared application failure** — backend/frontend/API contract failure.
4. **Gate-specific failure** — only the affected product/operational gate.
5. **Release-only failure** — tag, artifact, manifest, or publication issue.

A lower-level failure should not be duplicated as a new fix in every downstream workflow.

## 6. Three-level delivery topology

The product delivery model is:

```text
Vendor / Primary Seller
        │
        ├── owns platform source + release authority
        │
        ▼
Reseller / Secondary Seller
        │
        ├── receives a controlled distributable package
        ├── has tenant-scoped administration
        └── cannot become the platform release authority
        │
        ▼
Customer / End Customer
        │
        ├── receives customer-scoped deployment/package
        ├── cannot see vendor/reseller control-plane data
        └── operates only within assigned tenant/workspace boundaries
```

Release artifacts must eventually encode this distinction explicitly. A customer package is not the same artifact as the vendor source/release package.

## 7. Required release evidence

For each production release, retain:

- immutable Git tag;
- commit SHA;
- release notes;
- Production Certification run URL/ID;
- applicable Product Acceptance evidence;
- applicable Hardening/DR/Recovery evidence;
- deployment-tested revision;
- rollback evidence when performed;
- customer/reseller handoff manifest.

Never place credentials, private keys, production endpoints, or provider secrets in the release artifact.

## 8. Current roadmap alignment

The current project is in **Release / Final Handoff**, not in implementation or early product acceptance. Existing certification evidence should be reused unless a later code/configuration change invalidates the relevant gate.

The next implementation phases should therefore focus on:

1. CI/release topology stabilization;
2. required-check policy and failure observability;
3. vendor/reseller/customer artifact separation;
4. controlled customer handoff package;
5. external-production deployment evidence when a real target exists.

## 9. Definition of done for this topology

This topology is considered implemented when:

- production certification is not part of default PR CI;
- every workflow has one primary responsibility;
- release tags invoke release-grade certification;
- downstream workflows do not duplicate upstream gate logic without justification;
- failures can be classified by layer;
- release evidence is traceable to one immutable revision;
- vendor/reseller/customer delivery boundaries are represented in the release model.
