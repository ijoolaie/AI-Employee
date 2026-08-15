# Automatic Employee Memory Extraction & Consolidation — As-Built v0.2.26

## Purpose
Convert successful Employee Runs into durable memory candidates only when the Employee explicitly enables automatic extraction.

## Runtime
`Run -> successful output -> AIGateway(memory-extractor-v1) -> candidate validation -> secret filter -> semantic deduplication -> conservative consolidation/create -> audit`

## Policy
```json
{
  "memory": {
    "enabled": true,
    "auto_extract": true,
    "max_candidates": 5,
    "min_importance": 3,
    "dedup_threshold": 0.92
  }
}
```

All controls are bounded. The feature is opt-in and best-effort.

## Safety
- Never stores credentials, passwords, API keys, access/refresh tokens, or secret assignments detected by the guard.
- Tenant and Employee isolation is preserved.
- Candidate memory types are limited to `fact`, `preference`, `instruction`, `summary`.
- Candidate content is limited to 2,000 characters.
- Extraction failure is audited and logged but does not fail the parent Run.

## Consolidation
Candidates are compared only against active memories for the same Tenant, Employee, and memory type. Similarity at or above the configured threshold is treated as a duplicate. The system keeps the more informative representation and the higher importance instead of creating duplicate rows.

## Audit
- `memory.auto_extracted`
- `memory.auto_extract_failed`
- underlying `ai.provider_call`
- existing `memory.created` when a new memory is persisted

## Current limitation
The consolidation strategy is deterministic and conservative. It does not ask a second LLM to rewrite conflicting memories. Conflict-resolution/temporal memory policy can be added later.
