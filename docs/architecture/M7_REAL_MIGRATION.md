# M7 — Real Migration & Cleanup

## Goal
Turn the M1–M6 architectural boundaries into real code boundaries without
breaking existing APIs.

## What changed
- Every M2 bounded context now has explicit `domain`, `application`, and
  `infrastructure` packages.
- Module-owned application services can be introduced without importing legacy
  services.
- Existing legacy service paths remain compatibility facades until their callers
  have been migrated and tests pass.
- A migration manifest records the intentional transitional state.
- Architecture tests now distinguish allowed compatibility imports from forbidden
  new cross-module coupling.

## Migration order
1. Workflow orchestration
2. Knowledge/RAG/Memory
3. CRM
4. Commerce/Orders
5. Billing
6. Employees
7. Remove compatibility facades

## Safety rule
No mass rewrite. Each service is migrated as:
legacy implementation -> module application service -> adapter/port -> tests ->
caller migration -> facade deprecation.

## Important
This release does not pretend that an automated package move equals a complete
business-logic migration. The repository is prepared for real incremental
migration, and compatibility is intentionally preserved.
