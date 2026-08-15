# RC6 — Analytics, Employee Templates, Guardrails & GDPR

## Scope

RC6 completes the next sales-readiness layer across backend, frontend, onboarding/navigation, and documentation.

### Analytics / ROI
`GET /api/v1/analytics/roi` exposes tenant-scoped operational KPIs:
- conversations
- AI-resolved conversations
- human handoffs
- runs and successful runs
- orders and revenue
- AI-attributed orders/revenue when orders carry `metadata.source=ai`
- resolution and handoff rates

The Analytics dashboard surfaces conversation volume and influenced revenue alongside existing cost/reliability metrics.

### Employee Templates
`GET /api/v1/employee-templates` returns reusable templates. `POST /api/v1/employee-templates/{code}/install` creates a tenant-scoped Employee with initial prompt, tools and guardrails.

Templates included:
- Sales Assistant
- Customer Support Agent
- Order Assistant

Templates are intentionally starting points; tenant configuration remains versioned through EmployeeVersion.

### Guardrails
`GET/PUT /api/v1/employees/{employee_id}/guardrails` reads and publishes guardrails on a new immutable EmployeeVersion. Guardrails are stored in the existing `EmployeeVersion.rules` contract so the runtime can consume the same rules used by the AI Core.

Example controls:
- allowed tools
- maximum discount percentage
- approval-required actions
- forbidden actions
- human-required situations

### GDPR / Privacy
Tenant admins can export or anonymize a customer:
- `GET /api/v1/privacy/customers/{customer_id}/export`
- `DELETE /api/v1/privacy/customers/{customer_id}`

Deletion is an auditable anonymization operation for customer PII. Conversations remain structurally available for tenant audit while customer identifiers and message-level contact fields are scrubbed.

## Frontend changes

- `/analytics` now includes ROI cards.
- `/templates` provides Employee Template installation.
- Employee detail now exposes Guardrails.
- `/privacy` provides customer data export and anonymization controls.
- Sidebar navigation exposes Templates and Privacy & GDPR.

## Release rule

Every new option must update its related backend/API, frontend route, navigation, dashboard/workspace surface, onboarding where relevant, and documentation in the same release.

## Production notes

ROI attribution is conservative: only orders explicitly marked with `metadata.source=ai` are attributed to AI. A future event/attribution model should add first-touch, assisted-touch and campaign attribution rather than inferring causality from conversation counts.

GDPR deletion must be paired with a formal retention policy, DPA, subprocessors register, consent/cookie controls, and documented legal basis before EU production launch.
