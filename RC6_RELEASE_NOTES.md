# RC6 — Sales Readiness Layer

This release adds the next production-facing product layer: ROI analytics, reusable Employee templates, configurable guardrails, and tenant-scoped GDPR/privacy controls.

Every new option is surfaced in its related dashboard/workspace/navigation/onboarding surface and documented.

## Endpoints
- `GET /api/v1/analytics/roi`
- `GET /api/v1/employee-templates`
- `POST /api/v1/employee-templates/{code}/install`
- `GET /api/v1/employees/{employee_id}/guardrails`
- `PUT /api/v1/employees/{employee_id}/guardrails`
- `GET /api/v1/privacy/customers/{customer_id}/export`
- `DELETE /api/v1/privacy/customers/{customer_id}`
