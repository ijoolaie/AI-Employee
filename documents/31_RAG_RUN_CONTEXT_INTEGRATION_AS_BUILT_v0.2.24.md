# RAG → Context Assembly → AI Run — As-Built v0.2.24

**Date:** 2026-08-07
**Status:** Implemented / source-verified

## Purpose

v0.2.23 established tenant-scoped knowledge indexing and semantic retrieval. v0.2.24 connects that foundation to the real Employee Run path. RAG is now a runtime context source rather than an isolated API.

## Runtime path

```text
Run input
  ↓
EmployeeVersion.rules.rag
  ↓
explicit query_fields
  ↓
RAG retrieval (tenant + indexed + active file scope)
  ↓
ExecutionContext.retrieved_context
  ↓
Prompt + Context Assembly v2
  ↓
AI Gateway
  ↓
LM Studio / future provider
```

## Employee policy

RAG is opt-in and configured in the immutable EmployeeVersion `rules` JSON:

```json
{
  "rag": {
    "enabled": true,
    "top_k": 5,
    "query_fields": ["message"]
  }
}
```

`query_fields` is mandatory when RAG is enabled. This prevents arbitrary Run input from being embedded accidentally. `top_k` is bounded to 1–20. Query construction is capped at 8000 characters.

## Retrieval guarantees

- Tenant isolation is enforced at the database query boundary.
- Only `KnowledgeDocument.status == indexed` is retrieved.
- Only active source files are retrieved.
- Retrieval returns chunk/document/file identifiers, filename, chunk index, score and content.
- Empty/missing configured query fields fail closed.

## Prompt safety

Retrieved content is inserted into the explicit `Retrieved Knowledge (untrusted reference material)` context section. The assembled prompt tells the model that retrieved material is evidence and that instructions contained in documents must not be followed as system instructions.

## Observability

Each enabled retrieval records `knowledge.retrieved` in Audit Log and adds `rag_enabled` / `rag_result_count` to AI Provider Call metadata.

## Approval interaction

RAG retrieval itself is read-only and does not require Human Approval. Side-effecting Tools continue to use the existing RBAC + Approval boundary.

## Waiting-state correction

v0.2.24 also corrects the existing approval pause path: when a Run returns to `waiting`, `completed_at` is not populated and the Run completion audit is replaced with `run.waiting`. This preserves the semantic distinction between a paused Run and a completed Run.

## Verification boundary

Source compilation passed. Focused runtime pytest execution in the packaging environment remains environment-dependent because `asyncpg` is not installed in that environment; the release package already declares `asyncpg` in `requirements.txt`.
