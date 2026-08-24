# Public Repository Readiness — 2026-08-24

## Purpose

This document defines the gate for changing the GitHub repository from private to public. Public visibility is intentionally a separate decision from software readiness.

## Current audit observations

### Repository hygiene

- `.gitignore` excludes `.env` and `.env.*` while retaining `.env.example`.
- The repository contains test-only/local fixture credentials in development and CI configuration. These values are documented as non-production fixtures and must never be reused in production.
- The repository must contain no real customer data, production secrets, private keys or access tokens before visibility is changed.

### Git history

Current-tree inspection is not sufficient for publicization. Deleted files remain recoverable from Git history. Run:

```text
python scripts/public_repository_audit.py
```

The audit scans reachable Git blobs as well as the current tracked tree for common private-key and credential/token patterns.

### GitHub Actions and dependency security

- Existing CI/release workflows use least-privilege `contents: read` permissions for normal repository operations.
- A Dependabot configuration now covers pip, npm, GitHub Actions and Docker dependencies.
- A CodeQL workflow now covers Python and JavaScript/TypeScript analysis with only the required `security-events: write` permission.
- The publicization gate still requires GitHub-owner review of untrusted `pull_request_target` usage, secret exposure in logs, unnecessary write permissions, and whether GitHub's repository-level secret scanning/push protection/dependency-alert settings are enabled.

### Branch and PR exposure

Publicizing a repository also exposes its branch and pull-request history. Temporary/experimental branches were reviewed and stale/versioned branches with no unique commits ahead of the Phase 6 line were removed. `release/edition-model` is intentionally retained because it contains unique historical release-design commits.

Closed pull requests were reviewed at the metadata/diff level for representative older certification work; the reviewed PRs contain source/test/documentation changes and no identified production secrets or customer data. This is evidence for the current repository history review, not a guarantee against every possible future historical finding.

## Manual gates before Public visibility

- [x] `python scripts/public_repository_audit.py` passes with zero hard findings; the reported review items were addressed or intentionally retained.
- [x] No real credentials or customer data were reported by the current full-history public repository audit.
- [x] Temporary/experimental branches have been reviewed; flagged stale/versioned branches were deleted. `release/edition-model` remains as historical reference.
- [x] Closed PR history was reviewed for sensitive material; no identified production secrets or customer data were found in the reviewed historical PRs.
- [x] An explicit `SECURITY.md` exists and the intended vulnerability-reporting path is known.
- [x] License decision is made: **Apache License 2.0** is present at repository root.
- [x] README describes the product and current evidence boundary without claiming external production certification.
- [x] Repository-side dependency/security automation is present: Dependabot configuration plus CodeQL workflow.
- [ ] GitHub repository security settings still require owner-side review/enabling where available: secret scanning, push protection and dependency/security alerts.
- [ ] Repository settings still require owner-side review: branch protection/rulesets, tag protection, issue permissions and default branch.

## Evidence boundary

Local tests, local Docker production-like validation, local backup/restore and local recovery drills are valid local evidence. They are not substitutes for GitHub Actions execution, real production deployment, real payment/revenue evidence, external monitoring or production security certification.

## Decision

Do not change repository visibility until the remaining GitHub-owner settings are either PASS or intentionally accepted by the repository owner.
