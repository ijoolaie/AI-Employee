# Validation Layer — As-Built v0.2.14-LMSTUDIO

**Date:** 2026-08-07

## 1. Purpose

v0.2.14 hardens the JSON Schema contract boundary established in v0.2.12 and keeps it independent from the AI provider. Employee definitions declare `input_schema` and `output_schema`; the Run service validates input before creating a Run and validates the canonical model output before a Run can become successful.

## 2. Implemented component

`backend/app/services/schema_validation.py`

The module uses `jsonschema.Draft202012Validator` and `FormatChecker`.

Implemented behavior:

- Draft 2020-12 schema-definition validation.
- Runtime input/output validation.
- Nested object/array constraints.
- Required fields, types, enums, ranges and other standard Draft 2020-12 keywords supported by the library.
- `format` assertions through `FormatChecker`.
- Local JSON Pointer references such as `#/$defs/name`.
- Structured `ValidationAppError` responses with:
  - `field`
  - `path`
  - `schema_path`
  - `validator`
  - `message`
  - `validation_version`
- Bounded secondary errors: at most five are returned in the error details.

## 3. Security boundary

Employee schemas are application data and must not become an SSRF or filesystem-access primitive. External `$ref` and `$dynamicRef` values are therefore rejected. Only local fragment references beginning with `#` are accepted.

This is an intentional platform policy, not a limitation of JSON Schema itself. A future trusted-schema registry can introduce controlled external references without weakening tenant isolation.

## 4. Run lifecycle

```text
EmployeeVersion.input_schema
        ↓
Run input validation
        ↓
Run creation
        ↓
Prompt / Context Assembly
        ↓
AI Gateway / Provider
        ↓
canonical output {"text": ...}
        ↓
EmployeeVersion.output_schema
        ↓
Run success / failure
```

If output validation fails after successful provider execution, provider usage/cost remains recorded and the Run is marked failed through the existing audit/worker transaction path.

## 5. Verification

Focused validation suite: **10 passed**.

Coverage includes:

- valid payload;
- wrong type;
- required field;
- output contract;
- empty schema;
- invalid schema definition;
- nested constraints and enum;
- local `$ref`;
- external `$ref` rejection;
- `format: email` assertion.

Full pytest in the packaging environment remains blocked during collection because `python-jose` is not installed there. This does not affect the 10 passing validation tests.

The user's Windows PostgreSQL/Redis/Celery/LM Studio environment remains the authoritative runtime environment for E2E verification.

## 6. Long-term position

Validation is now a stable contract boundary for the future Tool Registry, RAG, Memory, Workflow and Human Approval layers. Those modules must reuse this service rather than implementing provider-specific or ad-hoc payload validation.
