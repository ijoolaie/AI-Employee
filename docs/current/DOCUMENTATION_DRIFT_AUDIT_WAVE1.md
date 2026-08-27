# Documentation Drift Audit — Wave 1

**Date:** 2026-08-27
**Status:** INITIAL INVENTORY COMPLETE / DEEP CODE AUDIT NEXT

## Repository documentation findings

### Current architecture

- V1.4 remains the frozen architecture baseline.
- V1.5 defines the Human + Agent operating-model extension.
- Productization roadmap identifies Unified Execution Foundation as the next implementation frontier.

### Code/documentation drift risks

1. The repository still contains substantial Employee-centric implementation terminology while V1.5 is Agent-first. This is an intentional migration gap, not yet evidence of completion.
2. Vendor/Reseller/Customer terminology coexists with Platform/Reseller/Client workspace terminology and requires a canonical vocabulary mapping.
3. Legacy v1.3/v1.3.1 planning documents are now classified historical and must not drive implementation.
4. Documentation search shows a large historical evidence set under older naming conventions; these remain evidence, not current design authority.

## Mandatory deep audit before Phase 8 completion

- Backend models and migrations
- API route inventory and authorization
- Employee/run execution paths
- Workflow/approval/schedule execution
- AI provider/runtime integration
- Frontend route and workspace boundaries
- RBAC and tenant isolation tests
- CI contract tests
- Deployment/runtime scripts

## Drift rule

No planned V1.5 capability may be marked AS-BUILT until code and relevant tests are identified.

## Next output

Produce a code-to-documentation traceability matrix mapping each canonical capability to:

- implementation location
- API surface
- UI surface
- test evidence
- CI evidence
- current classification
- identified gap