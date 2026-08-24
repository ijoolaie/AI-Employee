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

### GitHub Actions

The existing CI and release workflows use `permissions: contents: read` and do not require paid provider credentials in normal CI. The publicization gate still requires a manual review of every workflow for untrusted `pull_request_target` usage, secret exposure in logs, and unnecessary write permissions.

### Branch exposure

Publicizing a repository also exposes its branch and pull-request history. Temporary/experimental branches should be reviewed and removed or archived before the visibility change. The local audit flags branch names matching common temporary/versioned patterns for manual review.

## Manual gates before Public visibility

- [x] `python scripts/public_repository_audit.py` passes with zero hard findings; 10 review items were reported and addressed/retained intentionally (stale branches removed; `release/edition-model` retained as historical reference).
- [x] No real credentials or customer data were reported by the current full-history public repository audit.
- [x] Temporary/experimental branches have been reviewed; the flagged stale/versioned branches were deleted. `release/edition-model` remains because it contains unique historical release-design commits.
- [ ] Closed draft PRs do not contain sensitive material that should not become public.
- [x] An explicit `SECURITY.md` exists and the intended vulnerability-reporting path is known.
- [x] License decision is made: **Apache License 2.0** was added at repository root in commit `d9b499080c2860e993ed84f8db075191697eeabc`.
- [x] README describes the product and current evidence boundary without claiming external production certification.
- [ ] GitHub security features appropriate for a public repository are reviewed/enabled where available: secret scanning, push protection, dependency alerts and Dependabot configuration.
- [x] Actions workflows have been reviewed for least-privilege baseline; `contents: read` is used and no production provider credentials are required for normal CI.
- [ ] Repository settings are reviewed: branch protection/rulesets, tag protection, issue permissions and default branch.

## Evidence boundary

Local tests, local Docker production-like validation, local backup/restore and local recovery drills are valid local evidence. They are not substitutes for GitHub Actions execution, real production deployment, real payment/revenue evidence, external monitoring or production security certification.

## Decision

Do not change repository visibility until every manual gate above is either PASS or intentionally accepted by the repository owner.
