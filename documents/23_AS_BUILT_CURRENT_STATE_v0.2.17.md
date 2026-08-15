# Current State — As-Built v0.2.18

This is the current cumulative implementation snapshot. Historical v0.2.x files remain historical records; this document is the authoritative current-state summary for v0.2.18.

## Implemented

- RBAC + tenant isolation.
- Auth/JWT.
- Employee versioning.
- Run creation and asynchronous Celery execution.
- Windows asyncpg/Proactor lifecycle isolation using worker-local `NullPool`.
- Provider-agnostic AI Gateway.
- LM Studio local provider with Gemma 4 E4B.
- Prompt + Context Assembly.
- Hardened JSON Schema validation.
- AI Provider Call and Audit Log persistence.
- Run Trace API and frontend timeline.
- Usage/Cost summary API and frontend Usage page.
- Controlled Tool Registry with explicit JSON Schemas.
- Employee-level allowed-tool resolution and available-tools API.
- Bounded model → tool → model execution loop through the AI Gateway.
- LM Studio and Anthropic tool-call message support.
- Tool-call Audit Log events visible in Run Trace.
- Employee creation UI tool selection.

## v0.2.18 Tool implementation

Tool execution is intentionally bounded and fail-closed. The registry currently contains only the deterministic `calculator` and `current_time` tools. An EmployeeVersion exposes a tool only when its `allowed_tools` list names a registered tool. Tool arguments are validated against the registered JSON Schema. Run execution permits at most four model/tool iterations by default. Tool calls are recorded as `tool.call` audit events and therefore appear in the existing Run Trace without a database migration.

`GET /api/v1/employees/available-tools` returns registered schemas for Employee configuration. It does not execute tools.

## v0.2.17 Usage implementation

Usage is derived from existing `ai_provider_calls` records. No migration is required.

The reporting endpoint is:

`GET /api/v1/usage/summary`

The Customer Panel route is:

`/usage`

Metrics include calls, success/failure, prompt/completion/total tokens, recorded USD cost, average latency and provider/model breakdown.

The endpoint uses `audit.read` as its current administrative reporting permission. A dedicated billing/usage permission can be introduced when the broader permission and plan model is implemented.

## Verification status

- LM Studio smoke test: PASS (previously verified).
- Authenticated Run creation: PASS (201).
- Celery worker + PostgreSQL + LM Studio E2E: PASS.
- AI Provider Call persistence: PASS.
- Audit Log persistence: PASS.
- Run success commit: PASS.
- Backend source compilation for v0.2.18: PASS.
- Focused Tool Registry/provider tests: 6 PASS.
- Usage schema contract test: PASS.
- Frontend production build: environment-dependent; `node_modules` is intentionally not packaged.

## Not yet implemented

- External/dangerous Tool integrations, granular Tool RBAC and Human Approval for tools.
- Full RAG / Knowledge Base.
- Memory persistence.
- Human Approval.
- Quotas and hard limits.
- Billing/invoicing/payment.
- Workflow Engine.
- External integrations.

## Next step

The next technical stage should harden Tool security with granular permissions/approval policies before introducing external or side-effecting tools.
