# Prompt + Context Assembly — As-Built v0.2.13-LMSTUDIO

**Date:** 2026-08-07

## 1. Purpose

v0.2.13 introduces a dedicated Prompt + Context Assembly layer between Employee execution and the provider-agnostic AI Gateway.

The long-term architecture remains the planned separation:

```text
EmployeeVersion + validated Run input
        ↓
Context / Prompt Assembly
        ↓
Tool / RAG / Memory extensions
        ↓
AI Gateway
        ↓
Provider Registry
        ↓
LM Studio / Anthropic / future providers
```

The implementation in this release establishes the boundary without pretending that future Tool, RAG or Memory systems already exist.

## 2. As-Built components

### `backend/app/ai/prompt_assembly.py`

Provides:

- `ExecutionContext`
- `PromptAssembly`
- deterministic prompt-template rendering;
- stable JSON serialization for Run input;
- explicit system-context sections for rules, tenant context, retrieved context and memory;
- assembly metadata suitable for Trace/Audit;
- an explicit assembly version (`1`).

### `backend/app/services/run_service.py`

Now performs orchestration only:

1. loads the immutable EmployeeVersion referenced by the Run;
2. validates Run input;
3. constructs `ExecutionContext` from the current implemented context sources;
4. delegates prompt construction to `prompt_assembly`;
5. sends the resulting `ChatRequest` to `AIGateway`;
6. validates model output against the EmployeeVersion output schema;
7. persists Run status, usage and cost.

It no longer constructs the model messages directly.

## 3. Current context sources

| Context source | v0.2.13 status |
|---|---|
| Employee prompt template | Implemented |
| Run input | Implemented |
| Employee rules | Implemented |
| Tenant context | Extension point; empty in current Run flow |
| RAG/retrieved context | Extension point; empty |
| Memory | Extension point; empty |
| Tool definitions | Not implemented; no fabricated provider schemas |

## 4. Prompt rendering contract

Employee `prompt_template` continues to use Python format placeholders such as:

```text
Answer briefly about {message}.
```

The Run input has already passed JSON Schema validation before assembly.

If the template references an input field that is not present, assembly raises a structured `ValidationAppError` with the missing field names. This prevents an uncontrolled `KeyError` from escaping the execution layer.

## 5. Message contract

The current canonical message sequence is:

1. `system` — rendered Employee prompt plus populated context sections.
2. `user` — the validated Run input serialized as deterministic JSON.

The provider sees only the resulting provider-agnostic `ChatRequest`.

## 6. Tool policy

`EmployeeVersion.allowed_tools` already exists in the Employee contract. In v0.2.13 it is recorded as declared-tool metadata, but it is **not** converted into provider-specific tool schemas because a Tool Registry/executor does not yet exist.

This prevents the AI Core from claiming tool capabilities that the execution system cannot actually execute.

## 7. Observability

The Gateway remains the single owner of provider-call cost and latency.

v0.2.13 additionally records non-sensitive assembly metadata in:

- `AIProviderCall.raw_meta`
- `ai.provider_call` Audit metadata

Recorded metadata includes:

- `assembly_version`
- `prompt_version`
- message count
- effective tool-definition count
- declared Employee tool count
- populated context section names

Prompt text and raw Run input are **not** copied into these observability metadata fields.

## 8. Verification

- Python compilation: **PASS**
- Prompt assembly tests: **PASS (3)**
- Existing schema validation tests: **PASS (6)**
- Combined focused suite: **9 passed**
- Full pytest collection: **blocked by environment** because `python-jose` is not installed in the packaging environment; this is the same dependency limitation documented by previous releases.
- The user's Windows LM Studio/Gemma/Celery E2E path remains the runtime authority.

## 9. What remains planned

v0.2.13 does **not** implement:

- RAG retrieval;
- persistent Memory;
- Tool Registry or Tool execution;
- tenant policy injection beyond the explicit extension point;
- workflow context;
- human approval;
- provider failover.

Those capabilities can now be added behind the established assembly boundary without moving provider-specific code into RunService.


## v0.2.14 validation boundary

The assembly layer now consumes Run inputs only after the hardened Draft 2020-12 validation boundary. Prompt assembly itself remains provider-neutral and must not duplicate schema validation. See `25_VALIDATION_LAYER_AS_BUILT_v0.2.14.md`.
