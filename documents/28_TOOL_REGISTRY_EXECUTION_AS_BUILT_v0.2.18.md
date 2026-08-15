# Tool Registry & Controlled Execution — As-Built v0.2.18

## Purpose

This document records the implemented Tool Registry and controlled Tool execution boundary added after v0.2.17. The long-term architecture remains the source of truth for future capabilities; this document describes only what is actually shipped in v0.2.18.

## Implemented

- Provider-neutral `ToolCall` representation in `app/ai/schemas.py`.
- Code-based `ToolRegistry` in `app/ai/tool_registry.py`.
- Explicit registration with name, description, JSON Schema, handler and side-effect classification.
- Fail-closed behavior for unknown Employee `allowed_tools` names.
- JSON Schema validation before tool execution.
- Two deterministic built-in tools:
  - `calculator`: safe arithmetic parser; no Python eval/import/code execution.
  - `current_time`: current UTC timestamp from the worker.
- Employee prompt assembly now exposes only registered tools selected by the immutable EmployeeVersion `allowed_tools`.
- Bounded model → tool → model loop in `run_service.execute_run`.
- Maximum tool iterations controlled by `AI_MAX_TOOL_ITERATIONS` / `ai_max_tool_iterations`, default `4`.
- LM Studio OpenAI-compatible tool-call serialization and parsing.
- Anthropic tool-use/result serialization and parsing.
- Tool calls are audited as `tool.call` events with tool name, call id, iteration, latency and status; raw arguments/results are deliberately not stored in audit metadata.
- Existing Run Trace automatically surfaces these audit events; no new database table or migration is required.
- `GET /api/v1/employees/available-tools` exposes registered tool schemas to authenticated users with `employee.read`; it never executes a tool.
- Employee creation UI allows explicit tool selection.

## Security boundary

The model cannot select an arbitrary Python function. A tool must first exist in the registry and then be explicitly allowed by the EmployeeVersion. Tool arguments are validated against the registered JSON Schema. Unknown tools and invalid arguments fail closed. The initial built-ins have no external side effects.

Direct public tool execution endpoints are intentionally not implemented. All execution occurs inside the Run execution path after the AI response is received through `AIGateway.chat()`.

## v0.2.19 security hardening

- Every registered tool now declares a required permission code and approval requirement.
- The Celery worker re-authorizes tool calls from the Run creator's tenant-scoped roles; API-level RBAC is therefore not the only enforcement boundary.
- Missing tool permission fails closed and is audited as a failed `tool.call`.
- Tools marked `requires_approval` are blocked until an explicit approval signal exists; no implicit approval is inferred from model output.
- Available-tools API exposes the policy metadata so Employee configuration can show the security boundary.
- The current safe built-ins require `run.execute` and do not require human approval.

## Not yet implemented

- External API tools.
- File-system mutation tools.
- Browser tools.
- Database mutation tools.
- Per-tool granular RBAC/approval policies.
- Human approval for dangerous tools.
- Persistent Tool catalog in PostgreSQL.
- Tool billing/pricing.

## Verification

- Backend source compilation: PASS.
- Tool Registry + prompt assembly tests: PASS.
- LM Studio provider tool-message serialization/parsing test: PASS.
- Focused tool tests: **6 passed**.
- Full project test suite remains environment-dependent when packaged dependencies are absent.

## Architectural note

This release establishes the Tool boundary required by `10_AI_Core_v1.2` without prematurely introducing external side effects. The next tool-related hardening stage should be granular tool permissions, approval policies and durable tool-call spans before adding dangerous/external integrations.
