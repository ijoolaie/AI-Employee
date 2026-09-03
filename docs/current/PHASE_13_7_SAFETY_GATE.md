# Phase 13.7 — Agent Safety Gate

**Status:** Implemented as a deterministic engineering gate; CI/runtime evidence required before closure.

## Purpose

Phase 13.7 is the final Agent Runtime gate before Security Gate #2. It verifies the safety properties already established by Phases 13.1–13.6 without introducing a second execution path.

## Required checks

The gate evaluates:

1. **Tenant isolation** — observed tenant scope must contain only the contract tenant.
2. **Permission enforcement** — the existing authorization boundary must report success.
3. **Approval enforcement** — an explicitly required approval must be granted before the gate can pass.
4. **Timeout safety** — the runtime contract must use a positive timeout and the timeout probe must pass.
5. **Retry safety** — retry policy must be valid and the retry probe must pass.
6. **Evidence integrity** — evidence is limited to stable correlation/outcome fields.
7. **Negative-path coverage** — the negative safety suite must pass.
8. **Sensitive-payload rejection** — prompts, memory, embeddings, secrets, tokens, authorization material, tool arguments and failure details are rejected from gate evidence.

The implementation is deterministic and side-effect-free: it does not execute a tool, invoke a model, access credentials, mutate a Run, or execute arbitrary test code.

## Evidence boundary

A passing result is **engineering/product evidence only**. It does not claim production deployment, customer acceptance, or external security certification.

## Closure criteria

Before closing issue #241, attach CI evidence for the gate tests plus the existing Phase 13 runtime/observability evidence. Then run Security Gate #2 (#242), which is the Phase 13 exit gate.
