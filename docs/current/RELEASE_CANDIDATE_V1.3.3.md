# AI Employee v1.3.3 — Release Candidate

## Release identity

This release candidate is frozen from the reconciled current `main` head:

- Version: `v1.3.3`
- Candidate branch: `release/v1.3.3-candidate`
- Source commit: `e5c0f37a1a42b45659c966af4755aec1c7767a21`
- Release class: Engineering Release Candidate

The exact commit above is the source identity for this candidate. Later `main` commits must not be represented as this release identity.

## Scope

This candidate packages the current engineering baseline after the Stage 7 engineering gates and canonical production-status reconciliation. It is intended to establish an immutable release identity for subsequent external evidence.

Included engineering evidence includes:

- production-like infrastructure validation
- failure-recovery smoke validation
- incident-response drill simulation
- SLO/error-budget engineering contract
- provider integration preflight contract
- alert ownership/routing contract
- runtime tenant isolation/RBAC contract
- production network hardening contract
- production secret-management contract
- release-manifest and artifact-integrity controls
- retention and HITL approval-state implementation

## External acceptance boundary

This candidate is **not** proof of completed external production acceptance.

The following remain external/operator evidence gates:

- Vendor production deployment and acceptance
- Reseller production acceptance
- Customer production acceptance
- Live Stripe/Shopify provider validation
- Live alert paging and staffed incident response
- Measured production RPO/RTO and HA/failover evidence
- External secret-manager rotation/recovery execution
- Authenticated deployed DAST and independent penetration testing

## Required release evidence

The immutable candidate identity must be bound to:

1. exact Git commit/tag
2. release manifest
3. runtime and edition artifacts
4. SHA-256 checksums
5. container image digests where externally published
6. SBOMs
7. CI provenance/attestation evidence
8. migration identity

No external production acceptance claim may be inferred solely from CI or repository evidence.

## Status

**Engineering Release Candidate — EXTERNAL PRODUCTION ACCEPTANCE PENDING**
