# Phase 12.7 — Code & Security Hardening

**Status:** Planned gate before continuing Phase 13 implementation
**Owner:** Engineering
**Scope:** Backend security, Agent Tool safety, tenant isolation, storage, observability, reproducibility, and regression evidence

## Purpose

The deep code audit identified several gaps where newer feature layers do not yet enforce the same security and consistency guarantees already present in the platform core. Phase 12.7 closes those gaps without changing the overall roadmap direction.

## Blocking findings

### P0/P1 — Must be fixed before Production / external customer acceptance

1. **Guardrail authorization**
   - Protect Employee guardrail/policy mutation with an explicit privileged permission.
   - Add read/write permission semantics where appropriate.
   - Verify Owner/Admin allowed; ordinary users denied; cross-tenant access denied.

2. **Privacy authorization**
   - Protect customer privacy export and deletion/anonymization with explicit permissions.
   - Suggested permissions: `privacy.customer.read`, `privacy.customer.export`, `privacy.customer.delete`.
   - Verify ordinary users cannot perform destructive/privacy-sensitive operations.

3. **Central side-effect approval policy**
   - Make approval enforcement a runtime concern, not only a template/UI concern.
   - Classify tools as read-only, write, financial, or external side-effecting.
   - At minimum review/gate: `send_email`, `create_order`, `create_invoice`, order/invoice mutations, refunds, and external mutations.
   - Approval must be tenant-scoped, auditable, idempotent, expiry-aware, and fail-closed.

4. **Template ↔ Tool Registry contract**
   - Every `allowed_tools` entry in every Employee template must exist in the registry.
   - Resolve the current `add_to_cart` mismatch by either implementing/registering the tool or removing it from templates.
   - Add a CI invariant so an unknown tool makes CI fail.

## P1/P2 hardening

5. **File/storage quotas**
   - Enforce max file size, request size, files per request, and per-tenant storage quota.
   - Validate MIME/content and normalize filenames.
   - Enforce quota before consuming the complete upload.

6. **Metrics exposure**
   - Keep `/metrics` off the public application surface or protect it through internal networking/authentication/allowlisting.
   - Review whether any operational metric should be tenant-scoped or aggregated.

7. **Dependency reproducibility**
   - Introduce a deterministic dependency lock strategy (`requirements.in` + lock, or equivalent).
   - CI and release builds must install the locked graph.

8. **Version identity reconciliation**
   - Define Product Version, Backend Package Version, API Version, Git Tag, and Build SHA semantics.
   - Remove ambiguous/stale runtime version strings.
   - Health/version reporting should expose the intended build identity.

## Required security regression matrix

- Cross-tenant file access → denied
- Cross-tenant run access → denied
- Cross-tenant approval decision → denied
- Ordinary user → guardrail mutation → denied
- Ordinary user → privacy export → denied
- Ordinary user → customer deletion → denied
- Side-effect tool without required approval → denied
- Financial mutation without approval → denied
- Unknown template tool → CI failure
- Oversized upload → rejected
- Tenant quota exceeded → rejected
- Unauthorized metrics access → denied

## Acceptance criteria

Phase 12.7 is complete only when:

- All blocking findings are fixed.
- New security regression tests pass.
- Existing backend/frontend/CodeQL/architecture/observability gates remain green.
- Local real-stack evidence covers the affected authentication, worker, database, Redis, and Test Center paths.
- Documentation is reconciled with the actual main branch.
- A final hardening report records commit SHA, test evidence, and known residual risks.

## Relationship to roadmap

Phase 12.7 is a hardening gate, not a replacement for Phase 13. After this gate passes, continue the roadmap with:

### Phase 13 — Agentic Operating Model

- **13.1 Agent Runtime Contract:** formalize input/context/memory/tools/permissions/approval/timeout/retry/output/evidence contracts.
- **13.2 Agent Execution:** evolve the current worker boundary into controlled Agent execution without arbitrary `eval`/`exec` behavior.
- **13.3 Human-in-the-Loop:** integrate the hardened approval engine into Agent execution.
- **13.4 Agent Memory:** tenant-safe short/long-term memory and knowledge retrieval.
- **13.5 Agent Observability:** correlate request, tenant, user, employee, version, run, tool call, approval, and worker task.
- **13.6 Agent Evaluation:** extend Test Center into Agent evaluation with assertions, scoring, and immutable evidence.
- **13.7 Agent Safety Gate:** security, reliability, audit, rollback, and evidence gate before Phase 14.

### Phase 14

Continue the existing roadmap after Phase 13 passes its safety/evidence gate. Production and external customer acceptance require independent external evidence; green CI or local evidence alone is not customer acceptance.

## Engineering rule for future PRs

Every feature PR must explicitly document:

- Feature behavior
- Tenant isolation impact
- RBAC/permission impact
- Side-effect/approval impact
- Audit/evidence impact
- Tests
- Observability impact
- Rollback/migration impact

This keeps feature delivery and security/evidence work on the same track.