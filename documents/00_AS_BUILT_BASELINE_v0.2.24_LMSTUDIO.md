# As-Built Baseline v0.2.24-LMSTUDIO

This is the authoritative cumulative baseline for the v0.2.24 package. All prior implemented changes remain in scope unless explicitly superseded in CHANGELOG.md.

## Current AI path

EmployeeVersion + validated Run input → optional tenant-scoped RAG retrieval → Prompt + Context Assembly → Tool/Approval boundary → AI Gateway → provider registry → LM Studio / Anthropic.

## RAG state

The v0.2.23 Knowledge Base foundation is now runtime-connected. RAG is opt-in through EmployeeVersion.rules.rag and requires explicit query_fields. Retrieved chunks are limited to indexed documents belonging to the same tenant and active source files. Retrieved content is labeled untrusted reference material.

## Verification

- Source compilation: PASS
- Existing LM Studio/Celery/PostgreSQL end-to-end baseline: carried forward as verified
- RAG focused runtime tests: environment-dependent because the packaging environment used for release verification does not have asyncpg installed; asyncpg remains declared in backend requirements.
- Real .env: excluded from ZIP
- pycache/pyc: excluded from ZIP

## Planned but not yet implemented

Memory, scheduler/triggers, workflow engine, broader integrations, production vector-store migration, quotas/billing, and production security hardening remain future phases.
