# RAG / Knowledge Base Foundation — As-Built v0.2.23

## Purpose
This release establishes the first real Retrieval-Augmented Generation foundation while preserving tenant isolation and the existing AI Gateway boundary.

## Implemented
- Tenant-scoped `knowledge_documents` and `knowledge_chunks` persistence.
- File-to-knowledge indexing through `POST /api/v1/knowledge/index`.
- Text extraction for TXT/MD/CSV/JSON/XML/HTML.
- Optional PDF extraction through `pypdf`.
- Optional DOCX extraction through `python-docx`.
- Deterministic chunking with overlap.
- Embeddings through the configured LM Studio OpenAI-compatible `/v1/embeddings` endpoint.
- Development default embedding model: `text-embedding-nomic-embed-text-v1.5`.
- Tenant-scoped cosine-similarity retrieval through `POST /api/v1/knowledge/search`.
- Hard top-k limit of 20.
- Audit event `knowledge.indexed`.
- Storage remains tenant-namespaced through the existing file/storage layer.

## Deliberate v0.2.23 boundary
Embeddings are stored as PostgreSQL JSONB to avoid making pgvector a hard prerequisite for the local Windows/LM Studio development stack. The service boundary is intentionally isolated so a future release can move retrieval to pgvector or a dedicated vector store without changing the API contract.

This release does **not yet** inject retrieved chunks into Employee Run prompts automatically. That is the next RAG integration step after the foundation is verified.

## Security
- No client-supplied tenant_id is accepted.
- File access is tenant-scoped through existing RBAC.
- Knowledge retrieval is tenant-scoped in SQL before similarity scoring.
- Real `.env` files remain excluded from release packages.
