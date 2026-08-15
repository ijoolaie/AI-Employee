# M5 — Frontend Modularization

## Implemented
The frontend now has explicit domain boundaries matching the backend:

- Employees
- Workflow
- Knowledge
- CRM
- Commerce
- Billing

Each domain has:
- `index.ts` — domain entry point
- `api.ts` — API boundary
- `types.ts` — stable UI/domain contracts

A shared API client, event catalog, and domain registry were also added.

## Migration rule
Existing pages/components remain untouched in M5. New frontend work should
enter through the domain boundary instead of importing backend/transport details
directly.

## Why this is incremental
This avoids a large frontend rewrite. Existing UI continues to work while pages
and components are moved into their domain one feature at a time.

## Next
M6 adds CI architecture gates, checks frontend/backend boundary rules, and
creates a controlled deprecation path for legacy imports.
