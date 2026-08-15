# Employee Memory — As-Built v0.2.25

## Purpose

v0.2.25 adds the first durable Employee Memory layer. Memory is separate from the Knowledge Base: Knowledge stores external reference documents, while Memory stores tenant-scoped information intentionally associated with an Employee.

## Implemented

- `employee_memories` PostgreSQL table with:
  - tenant isolation
  - Employee association
  - optional source Run
  - memory type (`fact`, `preference`, `instruction`, `summary`)
  - content
  - embedding
  - importance 1–5
  - lifecycle status
  - metadata
  - optional expiry
  - creator/audit linkage
- LM Studio embedding reuse through the existing provider boundary.
- Semantic retrieval using the existing cosine-similarity foundation.
- Explicit memory policy in `EmployeeVersion.rules.memory`.
- Explicit `query_fields`; arbitrary Run input is never embedded implicitly.
- Bounded `top_k` and `min_score`.
- Memory is tenant-scoped and Employee-scoped. System Employees may have tenant-local memory; memory itself remains isolated by tenant.
- Runtime integration into `ExecutionContext.memory` and canonical Prompt + Context Assembly.
- Memory is presented to the model as context, not provider-level instructions.
- API:
  - `POST /api/v1/memory`
  - `POST /api/v1/memory/search`
  - `DELETE /api/v1/memory/{memory_id}`
- Permissions:
  - `memory.read`
  - `memory.write`
  - `memory.delete`
- Audit actions:
  - `memory.created`
  - `memory.retrieved`
  - `memory.deleted`

## Explicit safety decisions

Memory is **opt-in**. An EmployeeVersion without `rules.memory.enabled=true` does not retrieve memory. Retrieval requires explicit input fields. Memory does not automatically become a system instruction. Deletion is a soft delete so historical auditability is preserved.

## Not yet implemented

Automatic memory extraction from model output, memory consolidation/deduplication, user-facing memory review UI, and policy-driven automatic expiration are future work. Automatic extraction is intentionally not enabled in this release because storing model-generated facts without an explicit policy can create durable incorrect information.

## Verification

- Source compilation: PASS
- Focused memory context tests: PASS
- Full database runtime verification remains environment-dependent when asyncpg is unavailable in the packaging environment.
