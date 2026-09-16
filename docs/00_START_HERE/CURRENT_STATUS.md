# Current Status

**Last reconciled:** 2026-09-16
**Latest published release:** `v1.4.1`
**Release commit:** `f7f5062feb125c7ca50263f74a0e40bc4abfa591`
**Exact-SHA Production Certification:** Run `34696339261` — SUCCESS
**Current engineering mainline:** `main` at `1c8c3ee2fc933148f90e967e18167fe602d0ad00`
**Current status:** ENGINEERING MAINLINE ADVANCED / RELEASE CERTIFICATION BOUND TO v1.4.1 / EXTERNAL PRODUCTION GATES PENDING

## Executive truth

The AI Employee Platform is a multi-tenant business operating platform evolving toward a **Human + Agent operating model**. Platform, Reseller and Client workspaces remain separated by tenant, role and authorization boundaries.

`v1.4.1` remains the latest published exact-SHA certified release. Its certification is bound to `f7f5062...` only. Current `main` has subsequent Agent governance engineering commits and is **not** a newly certified release.

There is still no verified external production deployment of `v1.4.1` recorded in repository evidence.

## Current engineering validation

On 2026-09-16, the local backend suite was re-run from the repository root with PostgreSQL available:

- `pytest backend/tests -k "agent or workflow"` → **229 passed, 546 deselected**.
- `pytest backend/tests` → **775 passed**.

The concurrency test that initially failed because PostgreSQL was unavailable passed after the repository PostgreSQL service was started. This is repository engineering evidence, not external production evidence.

## Latest Stage 8 hardening

The mainline now includes the following merged governance work:

- **PR #514** — policy decisions are connected to the audit bridge and execution-trace metadata.
- **PR #516** — governed AgentInstance replacement workflow with explicit replacement proposals, cutover preparation, predecessor draining, lineage and governed cutover.
- **PR #517** — principal identity evidence is preserved through workflow child-run creation; merged as the current mainline commit `1c8c3ee...`.

These changes supersede the earlier Stage 8 audit records that still described replacement and workflow principal propagation as open gaps.

## Stage 8 position

Stage 8 is **not yet declared fully complete/certified**. The repository now has a substantially stronger governed workforce foundation, but the Stage 8 blueprint requires implementation, automated validation, operational evidence and documentation traceability together.

The remaining Stage 8 engineering/evidence focus is now narrower:

- complete principal identity evidence across all protected execution paths, not only workflow child propagation;
- complete tool allow-list / side-effect / approval-binding evidence against the governance checklist;
- complete agent-to-agent trust acceptance evidence;
- complete usage attribution, budget enforcement and runaway-execution evidence where not already covered;
- reconcile exact commit evidence and release-candidate certification for promoted Agent capability code.

## v1.4.1 release checkpoint

- PR #501 — Self-Hosted edition and release asset publication — merged.
- Release tag: `v1.4.1`.
- Release target SHA: `f7f5062feb125c7ca50263f74a0e40bc4abfa591`.
- Certification run: `34696339261` — SUCCESS.
- Certification job: `103560364112` — SUCCESS.
- Four edition packages plus runtime, manifest and SHA256SUMS were published.
- External deployment, live-provider acceptance and customer acceptance remain pending.

## Current Agent capability workstream

The architecture already contains the core mechanics for Tool Calling, structured tool arguments/schemas and bounded multi-step execution. The active work is to prove these capabilities with explicit acceptance contracts, provider-neutral safety boundaries and real-provider validation rather than reimplementing the runtime from scratch.

## Stage 7 external boundary

The following remain external-only gates: real production deployment, measured production SLO/SLI and error budget, backup/restore/DR RPO/RTO, live provider validation, deployed-target isolation/RBAC, DAST and independent security review, networking/TLS/secret lifecycle, HA/failure recovery, incident/on-call rehearsal and final customer acceptance.

## Evidence boundary

CI, repository tests, production-like validation and simulated providers establish engineering/release evidence. They do not establish live production deployment, measured production SLO/DR, independent security review or customer acceptance.

Certification never transfers automatically across SHAs.
