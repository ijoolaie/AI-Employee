# As-Built Baseline v0.2.27-LMSTUDIO

This is the authoritative cumulative baseline for the v0.2.27 package. All prior implemented changes remain in scope unless explicitly superseded in `CHANGELOG.md`.

## Current AI path

EmployeeVersion + validated Run input → optional tenant-scoped RAG retrieval → optional Employee Memory retrieval → Prompt + Context Assembly → Tool/Approval boundary → AI Gateway → provider registry → LM Studio / Anthropic.

Successful Runs may additionally execute the opt-in automatic memory extraction pipeline. Memory lifecycle now supports versioning, supersession, expiry and audit-preserved historical state.

## Memory lifecycle state

`employee_memories` now supports:

- `active`
- `superseded`
- `expired`
- `deleted`
- `conflict`

Each memory has a monotonic version number within an explicit supersession chain, an optional `supersedes_id`, and `effective_at` / `expires_at` lifecycle timestamps.

Retrieval only returns active, non-expired memories. Expired records are marked `expired` before retrieval results are calculated.

## Conflict resolution

Explicit memory creation may provide a `conflict_key` and/or `supersede_memory_id`. Matching active memories with the same tenant, Employee, memory type and conflict key are superseded by a new version rather than overwritten. Automatic extraction may ask the model for a stable `subject_key`; when present, that key becomes the lifecycle conflict key and the prior memory is preserved as `superseded`.

Semantic duplicates without a stable subject key continue to use the conservative consolidation behavior introduced in v0.2.26.

## Memory API

Existing endpoints remain:

- `POST /api/v1/memory`
- `POST /api/v1/memory/search`
- `DELETE /api/v1/memory/{memory_id}`

`POST /api/v1/memory` additionally accepts `conflict_key` and `supersede_memory_id`.

## Database delta

Migration `e8a1c4d7b902_memory_lifecycle.py` adds:

- `supersedes_id`
- `version`
- `effective_at`
- lifecycle status constraint
- self-reference index/foreign key

## Verification

- Python source compilation: PASS
- Migration source compilation: PASS
- Repository-wide pytest: BLOCKED in the packaging environment because runtime dependencies `asyncpg` and `python-jose` are not installed. This is recorded as environment-dependent rather than falsely reported as PASS.
- Real `.env`: excluded from ZIP
- `pycache` / `.pyc`: excluded from ZIP

## Planned but not yet implemented

- Memory management/review UI
- Scheduler and event triggers
- Workflow Engine runtime
- HTTP/API and webhook tools beyond the implemented tool surface
- Expanded observability
- Quotas and billing/invoicing
- Production vector-store migration
- Production security hardening
- Multi-provider production failover/routing

## v0.2.27 As-Built Audit

A code-versus-documentation audit was performed for this release. See `34_AS_BUILT_AUDIT_v0.2.27.md`.
