# W19 Voice & Visual Interaction

**Status:** DESIGN FOUNDATION — post-v1.4.16 mainline
**Issue:** #904
**Reconciled:** 2026-10-05

## 1. Purpose

W19 introduces provider-agnostic contracts for voice input/output and optional visual/avatar interaction.

Core Workforce execution must remain independent from media providers:

Workforce Core → governed media capability contract → provider adapter → media result

A provider must never become an alternate authorization or execution path.

## 2. First vertical slice

### Voice input

A voice-input request may carry:
- tenant scope;
- consent/policy state;
- language;
- audio format/duration metadata;
- provider-neutral request id;
- sensitivity classification.

The result may carry:
- transcript;
- confidence metadata;
- provider/model identity;
- latency/cost;
- explicit evidence status.

### Voice output

A TTS request may carry:
- tenant scope;
- text;
- language/voice requirements;
- policy/consent state;
- sensitivity;
- cost tier limit.

The result may carry:
- audio reference;
- duration;
- provider/model;
- latency/cost;
- evidence status.

Credentials must remain outside model context.

## 3. Visual boundary

Visual/avatar capabilities are presentation-only:
- avatar rendering;
- optional lip-sync;
- optional camera/video provider;
- optional image/video generation.

Camera capture is opt-in and must have an explicit privacy/consent boundary.

W19 does not perform biometric identification or infer sensitive identity attributes.

## 4. Provider governance

Provider selection must be capability-driven and fail closed.

The provider contract must expose:
- capability;
- provider/model;
- cost tier;
- latency metadata;
- data-retention/privacy declaration;
- tenant scope;
- request correlation;
- deterministic error classification.

No automatic provider fallback may occur after an execution has started.

## 5. Resource boundary

Voice/video workloads must not silently consume core application CPU/GPU resources.

Heavy media processing belongs behind an isolated worker/provider boundary with:
- bounded concurrency;
- tenant-aware quotas;
- cost accounting;
- timeout/cancellation;
- durable provenance.

Local GPU usage is optional and must not become a hidden production requirement.

## 6. Evidence states

VERIFIED, UNVERIFIED, UNKNOWN and NOT_APPLICABLE retain the same semantics established by W17/W18.

No transcript, audio, video, visual state or provider result may be presented as verified when it was generated only by a fixture or mock.

## 7. Definition of Done

semantic contract → provider interfaces → governance/cost/privacy boundary → registered capability path → tests → real-stack contract evidence → CI → documentation reconciliation

W19 remains post-v1.4.16 engineering work until a new exact-SHA Production Certification is run.
