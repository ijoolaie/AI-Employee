# Phase 14.7 — Security & Compliance Hardening

## Status

**Engineering baseline implemented.** This document maps the repository controls and regression evidence for tenant isolation, authorization, secrets handling, auditability, dependency/security policy, and negative paths.

This is **not** a compliance certification, penetration-test result, customer acceptance, or production security certification.

## Control map

| Control | Repository implementation | Evidence boundary |
| --- | --- | --- |
| Tenant isolation | Request context derives tenant from authenticated identity; authorization checks tenant ownership; marketplace imports clone into the target tenant | CI/unit evidence verifies selected negative paths; production isolation requires deployed evidence |
| RBAC | `require_permission(...)` dependencies and tenant-scoped role checks | CI/unit evidence; production authorization behavior remains deployment evidence |
| API-key scope | API-key requests carry explicit scopes and permissions are denied when a requested permission is absent | CI/unit evidence; credential lifecycle remains operational evidence |
| Marketplace isolation | Public imports become tenant-local definitions; source definitions are never referenced by imported installations | CI/unit evidence |
| Workspace collision prevention | Marketplace-generated slugs include a deterministic workspace scope suffix when a workspace is supplied | CI/unit regression evidence |
| Secrets handling | Marketplace import rejects secret-bearing policy fields instead of copying them across tenant boundaries | CI/unit negative-path evidence; secret-manager configuration remains deployment evidence |
| Auditability | Existing audit/event infrastructure remains the source of runtime action evidence | Repository contracts plus deployed audit-retention evidence |
| Dependency/security scanning | Dependabot, CodeQL and repository security workflows are part of the CI/release gate set | Workflow success is engineering evidence, not a compliance certification |

## Negative-path requirements

Security-sensitive changes must retain explicit tests for:

1. cross-tenant marketplace access denial;
2. non-owner publication denial;
3. duplicate installation scope denial;
4. invalid referenced agent definitions denial;
5. embedded secret-bearing marketplace policy denial;
6. workspace-scoped import identity uniqueness.

## Evidence rules

- CI, CodeQL, architecture validation and repository tests demonstrate that the checked commit satisfies the repository's engineering controls.
- Production security posture additionally requires deployed configuration, credential/secret-manager evidence, audit retention evidence, network and identity configuration, and operational incident evidence.
- No Phase 14.7 result should be described as SOC 2, ISO 27001, GDPR, penetration-test, customer-acceptance, or production-certification evidence unless the corresponding external evidence actually exists.

## Operational follow-up

For external production certification, collect evidence against the exact release commit, including deployed authorization behavior, tenant-isolation verification, secret-manager configuration, audit retention, vulnerability status, backup/recovery posture, and incident-response readiness.
