# Audit Baseline — 2026-08-27

## Repository truth

- Main development head was reconciled with the canonical documentation work.
- Release tags and published releases are tracked separately from certification/deployment truth.
- Historical V1.3/V1.3.1 planning records are classified as historical/superseded.

## Architecture truth

- V1.4: frozen architecture baseline.
- V1.5: Human + Agent operating-model extension.
- The repository remains Employee-centric in several existing backend/frontend paths; this is a known migration gap.

## Verified code surfaces discovered during audit

- `backend/app/models/employee.py`
- `backend/app/models/run.py`
- `backend/app/modules/employees/*`
- `backend/app/schemas/run.py`
- `backend/app/models/memory.py`
- `backend/app/schemas/workflow.py`
- `backend/app/models/conversation.py`
- `backend/app/api/v1/channel_webhooks.py`
- `frontend/app/(customer)/employees/[id]/page.tsx`
- `frontend/app/(customer)/runs/page.tsx`
- `frontend/app/(customer)/runs/[id]/page.tsx`
- `frontend/app/(customer)/chat/page.tsx`
- `frontend/app/(customer)/traces/page.tsx`
- `frontend/app/(customer)/developer/page.tsx`
- `frontend/app/(customer)/api-console/page.tsx`

## Gap classification

### AS-BUILT
Existing Employee, Run, workflow, memory, conversation and related UI/API surfaces.

### PARTIAL / VERIFY
Tenant/RBAC/workspace boundaries, approvals, tools, usage/cost and workflow integration require capability-level verification against tests and current runtime.

### PLANNED
WorkItem, AgentDefinition, AgentInstance, HumanExecutor abstraction, delegation/handoff, unified policy execution, Agent Teams and first-class Test Center.

## Next gate

Do not mark V1.5 execution foundation complete until each planned capability has implementation, API/UI contract where applicable, automated tests, CI evidence and updated documentation.
