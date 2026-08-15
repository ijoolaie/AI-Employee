# As-Built Baseline v0.2.19 — LM Studio

This is the current baseline after Tool Registry security hardening. It includes all prior v0.2.x implementations plus worker-side tool authorization and approval-policy enforcement.

The long-term architecture remains documented separately in the Master Plan, Architecture, AI Core, Employee Framework and Workflow documents. This file records only shipped behavior.

## Baseline

Auth/JWT, tenant isolation, RBAC, Employees/versioning, Runs, async PostgreSQL, Celery/Redis, AI Gateway, LM Studio/Gemma 4 E4B, Prompt/Context Assembly, JSON Schema validation, Audit Log, Run Trace, Usage/Cost reporting, controlled Tool Registry, bounded tool loop, and v0.2.19 tool authorization/approval policy enforcement.

## Security boundary

Tool execution requires registration, EmployeeVersion allow-list membership, valid arguments, required RBAC permission, and approval when a tool declares `requires_approval`. Current built-ins are deterministic and side-effect-free.

## Not shipped

External/browser/filesystem/database mutation tools, Human Approval UI/workflow, RAG, Memory, Workflow Engine, Quotas, Billing and external integrations.
