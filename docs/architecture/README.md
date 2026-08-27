# Architecture

Architecture documentation describes stable boundaries and decisions. It is separate from current implementation status.

## Principles

- Tenant context must be explicit at authorization and data-access boundaries.
- Authentication establishes identity; authorization establishes effective permissions.
- API-key scopes are an upper bound and must not expand RBAC permissions.
- Usage metering is tenant-scoped and idempotent.
- Audit events should be emitted from security- and billing-relevant flows.
- External provider integrations are isolated behind provider/application boundaries.
- Runtime evidence is separate from source-code claims.

## Current architectural focus

V1.4 is the active implementation baseline. Current execution priorities are correctness of tenant isolation, scoped authorization, idempotent usage accounting, and production evidence rather than introducing a new architectural generation.

## Status source

For what is actually implemented or currently blocked, see [Current Status](../current/STATUS.md).
