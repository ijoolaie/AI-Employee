# Stage 8 Acceptance Evidence — 2026-09-16

## Scope

This record is the acceptance-evidence companion to `STAGE_8_GOVERNANCE_AUDIT_CHECKLIST.md`. It distinguishes repository implementation and automated validation from external production certification.

**Baseline:** `main` at `1c8c3ee2fc933148f90e967e18167fe602d0ad00`

## Automated validation already executed on the baseline

- `pytest backend/tests -k "agent or workflow"` → **229 passed, 546 deselected**.
- `pytest backend/tests` → **775 passed**.
- The initial workflow concurrency failure was infrastructure-only (`PostgreSQL` unavailable); after starting the repository PostgreSQL service, the test passed.

## Acceptance evidence map

| Stage 8 control | Implementation evidence | Automated evidence | Repository status |
|---|---|---|---|
| Agent identity is tenant-scoped and first-class | `backend/app/models/agent_identity.py` | `test_agent_identity_lifecycle.py`, `test_agent_identity_policy_enforcement.py` | Verified |
| Lifecycle is explicit and fail-closed | `AgentInstanceStatus`, lifecycle transition service | `test_agent_instance_lifecycle_governance.py` | Verified |
| Revocation / kill switch blocks execution | `agent_policy_engine.py`, `agent_kill_switch_service.py` | governance/policy negative tests | Verified |
| Policy decision is auditable | `agent_policy_engine.py` → `agent_policy_audit.py` | `test_agent_policy_audit_bridge.py` | Verified |
| Workflow child principal is preserved | `Run.agent_instance_id` propagation | PR #517 tests | Verified |
| Governed AgentInstance replacement | `agent_workforce_replacement_service.py` and replacement API | PR #516 tests | Verified |
| Agent-to-agent delegation is governed | `agent_delegation_service.py` and policy engine | `test_agent_delegation_governance.py` | Verified for current repository scope |
| Tenant/memory execution boundaries | tenant-scoped execution and memory services | `test_agent_memory_boundary.py` and full suite | Verified for current repository scope |
| Tool allow-list / permission enforcement | `agent_policy_engine.py`, `tool_registry.py` | policy and tool governance tests | Verified for current repository scope |
| Approval binding | `ToolApprovalRequest` + policy checks for run/tool-call/arguments | approval/policy tests | Verified for governed approval path |
| Usage / cost visibility | usage API and optimization surfaces | usage-related backend tests | Implemented; operational target evidence remains external |
| Resource fairness / capacity limits | tenant fair scheduler and resource limiter | `test_phase_14_12_runtime_evidence.py` | Verified |
| Runtime load/capacity evidence | runtime load validation | `test_phase_14_13_load_capacity.py` | Verified |
| Tool Calling | `RunService` + AI Gateway + Tool Registry | agent/workflow suite | Core implemented |
| Structured tool arguments | Tool Registry schema validation | tool/schema tests | Core implemented |
| Bounded multi-step execution | bounded `tool_iterations` | workflow/agent tests | Core implemented |

## Items intentionally not promoted to production-certified status

The following require evidence outside the repository test environment and therefore remain external gates:

- production deployment identity;
- measured production SLO/SLI and error budget;
- real backup/restore/DR RPO/RTO;
- live provider acceptance on the deployed target;
- deployed Vendor → Reseller → Client isolation/RBAC;
- deployed-target DAST and independent security review;
- networking/TLS/secret lifecycle evidence;
- HA/failure recovery and incident/on-call rehearsal;
- final customer acceptance;
- exact-SHA release certification for code after the certified `v1.4.1` release.

## Acceptance decision

The repository has the governed workforce foundation required by Stage 8 implemented and covered by the current backend validation baseline. Remaining work is not a missing Stage 8 foundation; it is evidence/certification work at the repository and external-production boundary.

**Do not mark the production release gate complete from this document alone.** A later promoted commit must acquire its own exact-SHA certification evidence.
