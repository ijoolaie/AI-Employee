# Phase 6E Evidence Collection Runbook — 2026-08-27

## Purpose

Close the remaining Phase 6E external-production evidence gap without inventing deployment or acceptance evidence.

The repository currently provides example delivery manifests and controlled evidence templates. Delivery documentation explicitly says these are examples and must be replaced with approved contract/configuration inputs for real delivery.

## Evidence order

### 1. Vendor

Use the approved immutable vendor release identity first. Record:

- release/tag and source commit SHA
- artifact checksum
- deployment revision and UTC timestamp
- health checks for API/frontend/services
- migration head and successful migration output
- TLS/debug/CORS/trusted-host/security checks
- monitoring and alert test references
- backup and restore/recovery evidence
- Vendor authorization and privileged-action audit evidence
- operator acceptance/sign-off

Controlled form: `docs/evidence/phase6e/vendor-v1.2.0.md`

### 2. Reseller

Only after Vendor evidence is accepted, record:

- Vendor authorization/delegation reference
- immutable release/checksum
- reseller-owned secret/config ownership
- service health and migration evidence
- authorized-scope and entitlement-ceiling checks
- audit evidence for privileged actions
- monitoring, backup and recovery evidence
- operator acceptance/sign-off

Controlled form: `docs/evidence/phase6e/reseller-v1.2.0.md`

### 3. Customer

Only after the upstream delivery path is accepted, record:

- customer environment/release identity
- checksum and deployment revision
- service/migration health
- customer tenant-scope and authority checks
- entitlement enforcement
- privileged-action audit evidence
- monitoring/security/backup/recovery evidence
- rollback and support path
- customer acceptance/sign-off

Controlled form: `docs/evidence/phase6e/customer-v1.2.0.md`

## Evidence rules

- Never commit secrets, tokens, passwords, private keys, or customer data.
- Prefer immutable run IDs, timestamps, checksums, command output references, and sanitized screenshots/log references.
- Do not convert internal CI/product certification into Vendor/Reseller/Customer acceptance.
- Do not change a template's final decision to ACCEPTED without real environment evidence and an acceptance authority.
- Preserve the existing release identity; do not create a semantic `v1.4.0` release from the V1.4 execution baseline.

## Current boundary

Internal Production Certification run `33050378154` is a clean implementation/product-acceptance baseline with zero failed product gates. It does not substitute for Phase 6E external deployment acceptance.

## Exit criteria

Phase 6E external acceptance can be considered complete only when all three controlled evidence forms have populated identity, installation/health, security/authority, monitoring/recovery, handoff, and acceptance sections with real evidence references and named acceptance authority.

Until then the canonical status remains **EXTERNAL EVIDENCE PENDING**.
