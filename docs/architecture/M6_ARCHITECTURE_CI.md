# M6 — Architecture CI & Enforcement

## Implemented
- Machine-readable module boundary policy.
- Dependency checker with no third-party dependency.
- Backend cross-context import guard.
- Employee-to-context import guard.
- Infrastructure adapter guard.
- Frontend-to-backend/infrastructure guard.
- GitHub Actions workflow for pull requests and main/master pushes.
- Local developer command for the same architecture check.

## What this protects
The project can now reject architectural regressions automatically.
A developer can add functionality without silently reintroducing direct
coupling between CRM, Billing, Commerce, Workflow, Knowledge, Employees,
or infrastructure.

## Microservice readiness
M6 does not turn the project into microservices. It enforces the boundaries
required for selective extraction later. A module can be extracted when it
has an independent deployment/scaling requirement without first untangling
a large dependency graph.

## Deprecation strategy
Compatibility facades remain until real runtime migrations are verified.
They can then be removed in a dedicated cleanup release.
