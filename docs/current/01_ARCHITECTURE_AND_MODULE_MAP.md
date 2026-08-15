# Current Architecture & Module Map — 1.0.0-rc.8

## Backend modules

| Area | API | Main responsibility |
|---|---|---|
| Auth | `/auth` | registration, login, refresh, current user |
| Employees | `/employees` | employee definitions/versions |
| Runs | `/runs` | execution lifecycle |
| AI | internal gateway | provider abstraction, calls, cost/trace data |
| Files | `/files` | tenant-scoped file storage |
| Knowledge | `/knowledge` | RAG/knowledge foundation |
| Memory | `/memory` | memory lifecycle/search |
| Workflows | `/workflows` | workflow definitions/versions |
| Workflow Events | `/workflow-events` | event triggers |
| Schedules | `/workflow-schedules` | scheduled execution |
| Approvals | `/approvals`, `/workflow-approvals` | human gates |
| Orders | `/orders` | business order lifecycle |
| Sales | `/sales` | deals/pipeline |
| Invoices | `/invoices` | invoice lifecycle |
| Billing | `/billing`, `/billing-webhooks` | subscription/payment |
| Feedback | `/feedback` | user feedback |
| Usage | `/usage` | usage/cost visibility |
| Operations | `/operations` | developer/ops tooling |
| Admin | `/admin` | platform administration |

## Frontend route map

### Authentication
`/login`, `/register`

### Customer
`/dashboard`, `/employees`, `/employees/new`, `/employees/[id]`, `/runs`, `/runs/[id]`, `/files`, `/knowledge`, `/memory`, `/chat`, `/studio`, `/workflows`, `/workflows/[id]`, `/workflows/[id]/builder`, `/schedules`, `/approvals`, `/orders`, `/sales`, `/billing`, `/usage`, `/analytics`, `/traces`, `/developer`, `/api-keys`, `/webhooks`, `/settings`

### Admin
`/admin`, `/admin/tenants`, `/admin/validation`

## Data flow

### Simple AI execution
```text
UI → POST /runs → Run service → Celery → Employee Version
→ AI Gateway → provider → result/cost/trace → DB
→ UI polling → Run detail
```

### Workflow with approval
```text
Trigger → Workflow → Step Run → Approval required
→ pending approval → human decision → continue/fail
```

### Tenant isolation
```text
JWT → authenticated principal → tenant_id
→ service/repository filters → tenant-owned records only
```

## Reliability components

- transactional outbox
- retries/timeouts/cancellation
- DLQ/replay
- idempotency
- request correlation
- metrics
- OpenTelemetry
- rate limiting
- webhook replay protection
