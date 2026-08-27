# Canonical Product Vocabulary

**Date:** 2026-08-27
**Status:** CANONICAL

Use these terms in new code, APIs, UI and documentation.

| Canonical term | Meaning | Legacy aliases |
|---|---|---|
| Platform | Vendor-owned control plane and organization workspace | Vendor |
| Reseller | Organization operating a portfolio of Client tenants | — |
| Client | End-customer business tenant/workspace | Customer, End Customer |
| Human | Human user/workforce executor | Employee (when referring specifically to execution) |
| Agent | Specialized AI executor with explicit capabilities and policies | AI Employee |
| AgentDefinition | Reusable specification of an Agent | — |
| AgentInstance | Tenant-scoped deployed Agent | — |
| WorkItem | Canonical executable unit of work | Run (when run means business work) |
| Workflow | Ordered/orchestrated collection of WorkItems | — |
| Execution | An attempt to perform a WorkItem | Run (runtime record, where applicable) |
| Tool | Authorized external/internal capability available to an executor | Integration tool |
| Approval | Policy-controlled authorization checkpoint | — |
| Handoff | Transfer of execution context between executors | — |
| Test Center | Role-aware operational test and evidence surface | Test dashboard |

## Compatibility rule

Do not destructively rename legacy Employee/Run concepts solely for vocabulary. Existing APIs and database structures may remain during migration. New domain contracts must use canonical terms and explicit compatibility adapters.

## UI rule

Use business language first. Expose runtime terminology only in advanced/developer contexts.

## Workspace rule

Platform, Reseller and Client are the canonical workspace names. Vendor/Customer may remain in historical evidence only unless an API contract explicitly requires backward compatibility.
