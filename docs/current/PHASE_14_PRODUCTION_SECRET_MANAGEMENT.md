# Phase 14 — Production Secret Management, Rotation & Recovery

**Status:** Engineering contract complete / external secret-manager and rotation evidence pending  
**Date:** 2026-09-05

## Purpose

Establish a repository-verifiable boundary for production secrets without storing, printing, or testing real credential values in GitHub CI.

## Engineering controls

- Critical production secrets are required through environment substitution in `docker-compose.production.yml`.
- The production application rejects the known weak/default `SECRET_KEY` sentinel through its existing production configuration safety checks.
- Optional provider credentials are environment-sourced and have no checked-in credential material.
- Checked-in environment templates contain placeholders or empty values only.
- The CI contract validator never reads real secret values.
- The CI workflow does not inject production credentials and records only non-secret contract evidence.
- The repository explicitly records that external secret-manager validation, rotation execution, and recovery execution are still required.

## Required rotation contract for an external environment

For every production secret class (application signing/encryption key, database credential, Redis credential, provider/API credential, webhook signing secret, SMTP credential, and observability credential where applicable):

1. Create a new version in the approved secret manager without exposing the value to source control or CI logs.
2. Deploy the exact release SHA with the new secret version.
3. Verify application health/readiness and the affected integration.
4. Revoke or disable the previous secret according to the provider's safe overlap window.
5. Verify that the old credential can no longer authenticate where revocation is supported.
6. Record secret version metadata, release SHA, operator, timestamp, validation result, and rollback decision without recording secret values.

## Recovery contract

A real environment must demonstrate recovery from an unavailable or revoked secret by restoring the previous approved secret version or issuing a replacement, redeploying, and verifying health and affected workflows. The evidence must contain timestamps and outcomes, never the secret value.

## External boundary

Repository CI cannot prove:

- an operator-controlled AWS/Azure/GCP/Vault or equivalent secret manager is configured;
- production secret values are actually stored there;
- automatic/manual rotation has executed successfully;
- revocation has been tested against live providers;
- backup/recovery of secret versions works in the real environment;
- production operators, permissions, audit logging, and emergency access are correctly configured.

These remain **EXTERNAL-PENDING** until an operator-controlled staging/production environment exists.

## Evidence boundary

`production_certification_claimed=false`.

The engineering validator proves wiring and repository hygiene only. It intentionally does not request, print, compare, persist, or upload real secret values.
