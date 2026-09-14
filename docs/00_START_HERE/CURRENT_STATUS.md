# Current Status

**Last reconciled:** 2026-09-14
**Latest published release:** `v1.4.1`
**Release commit:** `f7f5062feb125c7ca50263f74a0e40bc4abfa591`
**Exact-SHA Production Certification:** Run `34696339261` — SUCCESS
**Current engineering mainline:** `main` after v1.4.1 release/documentation reconciliation
**Current status:** ENGINEERING-CERTIFIED RELEASE / EXTERNAL PRODUCTION GATES PENDING

## Executive truth

The AI Employee Platform is a multi-tenant business operating platform evolving toward a **Human + Agent operating model**. Platform, Reseller and Client workspaces remain separated by tenant, role and authorization boundaries.

`v1.4.1` is the current published release and its exact SHA passed the repository's Production Certification suite. Certification is bound to that SHA only. There is still no verified external production deployment of `v1.4.1` recorded in repository evidence.

## Stage 8 documentation reconciliation checkpoint

- Stage 8 governed Agent workforce engineering remains active.
- Workflow state-machine enforcement work has reached a stable repository validation state.
- Latest local validation evidence:
  - `759 passed`
  - no failing tests.
- Documentation reconciliation record:
  - `docs/00_START_HERE/DOCUMENTATION_RECONCILIATION_STAGE8.md`

This evidence confirms repository engineering state only. It does not change external production certification status.

## v1.4.1 release checkpoint

- PR #501 — Self-Hosted edition and release asset publication — merged.
- Release tag: `v1.4.1`.
- Release target SHA: `f7f5062feb125c7ca50263f74a0e40bc4abfa591`.
- Certification run: `34696339261` — SUCCESS.
- Certification job: `103560364112` — SUCCESS.
- Four edition packages plus runtime, manifest and SHA256SUMS were published.
- External deployment, live-provider acceptance and customer acceptance remain pending.

Historical `v1.3.8` remains frozen at `fd1e74b6b4c1701f7443efc202bad161ff19618c`.

## Latest hardening sequence

Key merged execution-boundary hardening includes PRs #464, #465, #466, #467, #468, #470, #473, #475, #477, #479, #482, #486, #487 and #499. These establish crash-safe handoff, approval/outbox safety, workflow replay fencing, durable execution leases, concurrent execution admission fencing and workflow FK integrity without weakening repository controls.

## Current Agent capability workstream

The next focused engineering work is **Tool Calling + Structured Arguments + Multi-step execution**. These are substantially implemented in the current architecture; the objective is to turn the existing capability into explicit acceptance contracts and provider-neutral guardrails.

## Evidence boundary

CI, repository tests, production-like validation and simulated providers establish engineering/release evidence. They do not establish live production deployment, measured production SLO/DR, independent security review or customer acceptance.

Certification never transfers automatically across SHAs.
