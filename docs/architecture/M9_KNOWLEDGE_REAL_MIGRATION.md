# M9 — Knowledge / RAG / Memory Real Migration

## Migrated
- KnowledgeDocument domain model
- KnowledgeChunk domain model
- Document and chunk repository ports
- Parser and embedding provider ports
- KnowledgeApplicationService
- Document ingestion lifecycle
- `knowledge.document.ingested` event
- Legacy parser/embedding adapters
- Unit tests

## Compatibility
Existing RC8 knowledge/RAG implementations are preserved behind adapters.
No database schema migration is introduced by this structural migration.

## Next
M10 should migrate CRM/Customer Experience using the same pattern.
