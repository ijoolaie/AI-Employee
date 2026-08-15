# Frontend Enterprise Dashboard v0.9.5

## Implemented
- Customer operations dashboard remains API-backed and now has dedicated Analytics.
- AI Chat executes real `/runs` through the existing authenticated API and polls run status.
- Trace Explorer loads `/runs/{id}/trace` and renders provider/model/tool/memory/planner events.
- AI Studio creates employees with prompt, output schema, allowed tools and autonomous runtime rules.
- API & Integrations page documents the existing bearer/OpenAPI contract without inventing unsupported API-key CRUD.
- Developer Console retains tenant-scoped metrics, audit logs, recent runs and dead-letter replay.
- Platform Admin retains tenants, validation and platform-wide dashboard.
- Customer navigation grouped around AI employees, workflows, runs, approvals, knowledge, memory, analytics, developer and integrations.
- Mobile navigation is available through the header selector while the full sidebar is used on desktop.

## Backend contract principle
The frontend only calls endpoints present in the shipped backend. Unsupported features such as long-lived API-key CRUD are surfaced as integration requirements rather than fake client-side credentials.

## Verification
`frontend/scripts/test-frontend-contract.mjs`: 49 passed, 0 failed.

A full Next.js build was not executed in the sandbox because the package registry could not install the project's declared dependency set (`@hookform/resolvers` returned HTTP 404). The application should be built in the project's normal development environment after `npm install` succeeds.
