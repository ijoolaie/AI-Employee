# Planned vs As-Built Audit — v0.2.27

## Purpose

This audit compares the current source tree against the long-term project documentation and the cumulative v0.2.x As-Built records. It is based on the actual files in the v0.2.27 package, not on planned documentation alone.

## Status legend

- ✅ Complete: implemented in source and represented in the current As-Built record.
- 🟡 Partial: meaningful foundation exists, but the documented production capability is not complete.
- 🔴 Not implemented: no production implementation found in the current source tree.
- ⚠️ Documentation mismatch: source and authoritative documentation disagree.

## Core / AI execution

| Area | Status | Evidence / assessment |
|---|---|---|
| RBAC / tenant isolation | ✅ | Permission dependencies, tenant-scoped services and prior verification records. |
| Provider-agnostic AI Gateway | ✅ | `app/ai/gateway.py`, provider registry and provider implementations. |
| LM Studio | ✅ | Local provider and existing smoke-test baseline. |
| Celery Run execution | ✅ | `app/workers/run_worker.py` and verified prior runtime path. |
| Prompt + Context Assembly | ✅ | Canonical assembly includes rules, RAG and Memory reference context. |
| JSON Schema validation | 🟡 | Foundation exists; broader output/schema policy remains limited. |
| Tool Registry | 🟡 | Registry/execution boundary exists; broader production tool ecosystem remains future work. |
| Human Approval | 🟡 | Approval infrastructure exists; generalized workflow-level approval remains future work. |
| Durable Email Outbox | ✅ | Implemented and documented in prior baseline. |

## RAG / Knowledge

| Area | Status | Assessment |
|---|---|---|
| Knowledge document/chunk storage | ✅ | Implemented. |
| Text extraction | ✅ | Implemented for supported document formats. |
| Embeddings | ✅ | LM Studio embedding path implemented. |
| Tenant-scoped retrieval | ✅ | Retrieval filters by tenant and indexed/active state. |
| Run context integration | ✅ | Retrieved knowledge is assembled as untrusted reference context. |
| Production vector store | 🟡 | JSONB embedding storage is the current implementation; pgvector/vector DB migration remains future scale work. |

## Memory

| Area | Status | Assessment |
|---|---|---|
| Durable Employee Memory | ✅ | `employee_memories`. |
| Tenant + Employee isolation | ✅ | Service queries scope both tenant and employee. |
| Semantic retrieval | ✅ | LM Studio embeddings + cosine similarity. |
| Runtime prompt integration | ✅ | Memory is reference context, not provider instruction. |
| Automatic extraction | ✅ | Opt-in, bounded, best-effort. |
| Secret filtering | ✅ | Pattern-based extractor guard. |
| Semantic deduplication | ✅ | Existing v0.2.26 behavior retained. |
| Versioning | ✅ | `version` + `supersedes_id`. |
| Supersession | ✅ | Explicit and subject-key driven. |
| Expiry | ✅ | Retrieval excludes expired records and lifecycle marks them expired. |
| Conflict-key policy | ✅ | Explicit `conflict_key` and extractor `subject_key`. |
| Historical audit | ✅ | Supersession/expiry/delete/create events. |
| Memory review UI | 🔴 | No dedicated management UI found. |

## Workflow / Automation

| Area | Status | Assessment |
|---|---|---|
| Single Employee Run | ✅ | Implemented. |
| Workflow Engine runtime | 🔴 | No production workflow runtime matching the master plan found. |
| Multi-step orchestration | 🔴 | Not implemented as a generalized engine. |
| Scheduler / Celery Beat workflows | 🔴 | No workflow scheduler implementation found. |
| Event triggers | 🔴 | Not implemented. |
| Replay / compensation | 🔴 | Not implemented. |

## Integrations / Product

| Area | Status | Assessment |
|---|---|---|
| SMTP email | ✅ | Implemented with durable outbox and approval boundary. |
| HTTP/API tool | 🔴 | No generalized production HTTP tool found. |
| Webhooks | 🔴 | Not implemented. |
| Broader CRM/messaging integrations | 🔴 | Not implemented. |
| Usage/cost reporting | ✅ | Existing read-only usage surface is present. |
| Quotas | 🔴 | Planned. |
| Billing/invoicing | 🔴 | Planned. |

## Security / Operations

| Area | Status | Assessment |
|---|---|---|
| RBAC | ✅ | Implemented. |
| Tenant isolation | ✅ | Implemented in core paths. |
| Secret-in-ZIP exclusion | ✅ | Real `.env` excluded. |
| Audit logging | ✅ | Core actions and AI/provider/memory events are recorded. |
| Production security hardening | 🟡 | Important foundations exist, but the full security document describes a larger production target. |
| Observability / Trace | 🟡 | Run Trace exists; generalized production observability remains incomplete. |
| CI/CD | 🔴 | No complete production CI/CD implementation found in the package. |

## Documentation findings

### ⚠️ Fixed in v0.2.27

- `00_AS_BUILT_BASELINE_v0.2.26_LMSTUDIO.md` incorrectly identified itself as the v0.2.25 baseline in its title/body. v0.2.27 corrects this in the new authoritative baseline.
- `23_AS_BUILT_CURRENT_STATE_v0.2.26.md` also retained a v0.2.25 title. v0.2.27 replaces it with an authoritative current-state document.
- v0.2.26 documentation described automatic consolidation but explicitly deferred conflict/temporal policy; v0.2.27 now records the implemented lifecycle/versioning policy.

### Historical documents

Older v0.2.x As-Built documents are retained intentionally as historical snapshots. They are not treated as the current implementation authority.

## Overall position

The project has moved beyond the original Core skeleton. The current codebase has a functioning AI execution path with RBAC, provider abstraction, local LM Studio execution, asynchronous Run execution, Tool/Approval boundaries, durable email delivery, RAG retrieval, Employee Memory retrieval, automatic Memory extraction and now Memory lifecycle/versioning.

The largest remaining gap between the long-term product vision and the actual implementation is no longer basic AI execution. It is **product orchestration and SaaS operational depth**: Workflow Engine, scheduling/triggers, broader integrations, quotas/billing, management UI, production observability/security and scale-oriented vector storage.
