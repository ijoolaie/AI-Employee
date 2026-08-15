# As-Built Baseline v0.2.26-LMSTUDIO

This is the authoritative cumulative baseline for the v0.2.26 package. All prior implemented changes remain in scope unless explicitly superseded in CHANGELOG.md.

## Current AI path

EmployeeVersion + validated Run input → optional tenant-scoped RAG retrieval → optional Employee Memory retrieval → Prompt + Context Assembly → Tool/Approval boundary → AI Gateway → provider registry → LM Studio / Anthropic.

## RAG state

Knowledge Base indexing and tenant-scoped retrieval are runtime-connected to Employee Runs. RAG is opt-in through `EmployeeVersion.rules.rag` and requires explicit query fields.

## Memory state

Durable Employee Memory is now implemented. Memory is stored per tenant and Employee, uses embeddings for semantic retrieval, and is opt-in through `EmployeeVersion.rules.memory`. The policy requires explicit query fields, bounded `top_k`, and `min_score`. Memory is assembled as reference context and is never promoted to provider-level instructions.

## Memory API

- `POST /api/v1/memory`
- `POST /api/v1/memory/search`
- `DELETE /api/v1/memory/{memory_id}`

Permissions: `memory.read`, `memory.write`, `memory.delete`.

## Verification

- Source compilation: PASS
- Focused memory policy/context tests: PASS
- Existing LM Studio/Celery/PostgreSQL end-to-end baseline: carried forward as verified
- Full DB runtime verification remains environment-dependent when asyncpg is absent from the packaging environment.
- Real `.env`: excluded from ZIP
- pycache/pyc: excluded from ZIP

## Planned but not yet implemented

Automatic memory extraction/consolidation, memory review UI, scheduler/triggers, workflow engine, broader integrations, production vector-store migration, quotas/billing, and production security hardening remain future phases.

## v0.2.26 Delta
Automatic Employee Memory Extraction & Consolidation is now implemented as an opt-in, best-effort post-run capability. See `33_AUTOMATIC_MEMORY_EXTRACTION_AS_BUILT_v0.2.26.md`.
