# RC8 LM Studio Tool-Calling Verification

## Status: PASSED

**Verified:** 2026-08-21  
**Environment:** Windows 11 + Docker Desktop / WSL2  
**Release context:** RC8 / current mainline  
**Provider:** `lm_studio`  
**Model:** `google/gemma-4-e4b`

This verification records the real end-to-end tool-calling test executed after switching the Docker Compose AI configuration from a fixed deterministic provider to environment-configurable provider/model settings.

## 1. Compose configuration

The `api`, `worker`, and `beat` services now accept:

- `AI_DEFAULT_PROVIDER: ${AI_DEFAULT_PROVIDER:-deterministic}`
- `LM_STUDIO_BASE_URL: ${LM_STUDIO_BASE_URL:-http://host.docker.internal:1234/v1}`
- `AI_DEFAULT_MODEL: ${AI_DEFAULT_MODEL:-google/gemma-4-e4b}`

The local test environment used:

```text
AI_DEFAULT_PROVIDER=lm_studio
AI_DEFAULT_MODEL=google/gemma-4-e4b
LM_STUDIO_BASE_URL=http://host.docker.internal:1234/v1
```

`docker compose config` resolved the expected values successfully.

## 2. Container verification

The following services were healthy/running:

- PostgreSQL — healthy
- Redis — healthy
- API — healthy
- Frontend — healthy
- Celery worker — running
- Celery beat — running
- Storage init — completed successfully

The API, worker, and beat containers all reported the same provider/model configuration.

## 3. LM Studio connectivity

From inside the API container:

`GET http://host.docker.internal:1234/v1/models` → `200 OK`

Available models included:

- `google/gemma-4-e4b`
- `text-embedding-nomic-embed-text-v1.5`

Therefore Docker → Windows host → LM Studio connectivity was verified.

## 4. Real Run execution

A real Run was created for employee:

- Employee: `RC8 Sales Agent`
- Employee slug: `rc8-sales-agent`
- Employee version: `3`
- Run ID: `7ee8ca02-3d31-45f5-835b-16eb4bbcbfee`

Input:

> Calculate 1234 * 56 using the calculator tool and give me the result.

Initial state: `pending`

Final state: `success`

## 5. Tool-calling result

The run successfully declared and executed the calculator tool.

- Tool: `calculator`
- `approval_required=false`
- Required permission: `run.execute`
- Tool iteration: `1`
- Tool call latency: `2 ms`
- Tool status: `success`

Final model output:

> The result of $1234 \\times 56$ is **69,104**.

The arithmetic result was correct: **69,104**.

## 6. AI provider trace

The trace contained successful provider calls for:

- Provider: `lm_studio`
- Model: `google/gemma-4-e4b`
- Tool count: `1`
- RAG: disabled for this test
- Prompt version: `3`
- Assembly version: `3`
- Declared tool count: `1`

Provider calls:

| Iteration | Prompt tokens | Completion tokens | Latency |
|---:|---:|---:|---:|
| 0 | 119 | 77 | 20,265 ms |
| 1 | 165 | 24 | 2,153 ms |

Total recorded tokens: **385**  
Total cost: **$0.00**

## 7. Trace events

The run trace successfully recorded:

- `run.created` — success
- `ai.provider_call` — success
- `tool.call` — success
- `ai.provider_call` — success
- `run.completed` — success

## 8. Worker verification

Celery worker successfully registered and executed:

- `run.execute`
- `email.send`
- `outbox.dispatch`
- workflow tasks

The worker log recorded the real `run.execute` task and two successful HTTP calls to LM Studio's `/v1/chat/completions` endpoint, followed by `run_finished`.

`celery inspect active` returned an empty active list after completion, confirming no stuck task remained.

## Final result

**RC8 LM Studio real tool-calling E2E test: PASS**

This verification is stronger than the earlier smoke test because it validates not only provider connectivity and run completion, but also the complete LLM → tool declaration → calculator execution → second LLM call → final response path.

> Note: RAG was intentionally disabled in this scenario. This document certifies LM Studio provider connectivity and calculator tool-calling, not the RAG pipeline.
