# AI Model Routing Architecture — post-v1.4.16

Status: engineering foundation
Release certification: NOT CLAIMED
External provider execution: NOT VERIFIED by this slice

## Purpose

The AI Employee runtime must not bind the whole company to one LLM provider. A task should be routed to the best operator-approved model/provider for that task, while preserving the existing tenant, approval, audit, budget and provider-boundary controls.

The routing rule is:

Business request
    ↓
deterministic Tool / Rule check
    ↓
Run + governed execution context
    ↓
Task classification / routing context
    ↓
AI Model Router
    ↓
operator-approved provider + model
    ↓
AI Gateway
    ↓
provider adapter
    ↓
AI result / tool call

## Non-negotiable boundaries

1. Tool before model. A deterministic business lookup should use its governed tool directly instead of consuming an LLM call.
2. Provider selection is operator-controlled. Request/tool arguments cannot select an arbitrary provider.
3. Model selection is policy-controlled. A caller-supplied model is only a compatibility input; when routing is enabled, the router may override it with an operator-configured candidate.
4. No blind fallback after a provider call starts. An ambiguous provider outcome remains UNKNOWN under the existing durable AIProviderCall execution fence. Retrying through another provider is not an automatic recovery mechanism.
5. No certification transfer. This engineering slice does not change the immutable v1.4.16 production certification boundary.
6. No fake provider evidence. Deterministic providers remain test-only and cannot be represented as external customer/provider execution.

## Routing dimensions

The initial deterministic router accepts:

- task class
- tool-calling requirement
- vision requirement
- structured/JSON requirement
- sensitivity class
- maximum cost tier

The operator configures candidate provider/model pairs with priority and capability metadata. The first implementation intentionally does not claim that any new external provider is live.

Future candidates can include local inference, low-cost/free APIs and paid providers without changing the business execution contract.

## Planned task classes

- general
- tool_calling
- reasoning
- rag
- memory_extraction
- planning
- vision
- structured_extraction

These are routing hints, not permissions.

## Provider lifecycle

Each provider remains an adapter implementing the existing AIProvider contract:

- chat()
- cost estimation
- explicit execution capabilities

Adding Groq, Gemini, Mistral or OpenRouter later means adding a named adapter and operator configuration. It does not mean allowing an Agent or tenant to choose a provider by putting a provider name in tool arguments.

## Observability

Every routed call should retain:

- routing policy version
- task class
- selected provider
- selected model
- selection reason
- number of eligible candidates
- normal provider-call latency/tokens/cost
- existing Run/tool/audit correlation

This makes model quality, latency, cost and failure rates measurable before any learned routing policy is introduced.

## Future adaptive routing

A later phase may add measured provider health and historical quality:

score = quality × Wq + reliability × Wr + latency × Wl - cost × Wc

The learned component must remain subordinate to deterministic governance: allowed providers, tenant policy, sensitivity, approval requirements, budgets and capability constraints are hard filters, not suggestions.

The router must never become a mechanism for bypassing authorization or approval.

## Implementation sequence

1. Router core — deterministic policy and operator allowlist.
2. Provider adapters — named adapters for selected external/local providers.
3. Health telemetry — latency, error/rate-limit state and cost.
4. Quality telemetry — tool success, validation failure, human correction, outcome/CSAT where available.
5. Adaptive scoring — only after sufficient evidence exists.
6. Tenant-level routing policy — only with explicit governance and budget controls.

The current slice implements step 1 only.