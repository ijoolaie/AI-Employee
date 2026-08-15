# Planned vs As-Built Audit — v0.2.28

## New milestone

The largest previous Core gap was the Workflow Engine. v0.2.28 closes only the first slice of that gap.

| Area | Status | Reality |
|---|---|---|
| Versioned Workflow definition | ✅ | Implemented |
| Manual Workflow trigger | ✅ | Implemented |
| Linear Employee Action steps | ✅ | Implemented |
| Context propagation | ✅ | Implemented |
| Step retry count | 🟡 | Bounded retry loop exists; backoff/advanced policy remains |
| Workflow trace/state | ✅ | Durable WorkflowRun + WorkflowStepRun |
| Schedule / Celery Beat | 🔴 | Not implemented |
| Event triggers | 🔴 | Not implemented |
| Condition step | 🔴 | Not implemented |
| Loop step | 🔴 | Not implemented |
| Wait/Approval step | 🔴 | Not implemented as generalized Workflow step |
| Timeout enforcement | 🔴 | Not implemented |
| Compensation / replay | 🔴 | Not implemented |
| Parallel steps | 🔴 | Not implemented |
| Visual builder | 🔴 | Not implemented |

## Overall project position

The platform now has a usable vertical path from Employee execution to a minimal orchestration layer. The next highest-value Workflow increment is **Condition + Schedule**, because these unlock useful automation without requiring the full visual/parallel engine.

The longer-term SaaS gaps remain quotas/billing, production observability/security, management UI, broader integrations and scale-oriented vector storage.
