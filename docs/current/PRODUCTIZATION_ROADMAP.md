# AI Employee Platform — Productization & Delivery Roadmap

## Roadmap truth — 2026-09-16

Three axes remain independent:

- **Release:** `v1.4.2` at exact SHA `dba0bb672deb1236b6724bb8851526e656f47967`, certified by Production Certification Run `35108008066`.
- **Architecture:** `V1.5 Agentic Operating Model`.
- **Engineering:** Stage 7 external production execution, Stage 8 governed Agent workforce foundation, and Stage 9 optimization/control loops.

`v1.4.2` is the latest published exact-SHA certified release. Current `main` may contain documentation reconciliation commits after that SHA; those commits are not automatically certified as a new release.

## Current position

Phase 11 Unified Execution is complete. Phase 12 Test Center is operationally hardened. Phase 13 Agent Teams & Marketplace is engineering complete. Phase 14.1–14.16 tracked engineering is complete/reconciled. PRs #521–#530 completed the current Stage 9 implementation/release-certification sequence, with PR #530 fixing the workflow approval certification blocker.

The project has now entered a dedicated **Commercial Readiness & External Production** phase. The default next work is evidence, deployment, security and operational validation—not broad feature expansion.

## Commercial Readiness Gate

### Objective

Prove that the certified product can be operated safely, observably and recoverably in a real production environment and can pass the required partner/customer acceptance gates.

### Required gate sequence

1. **Readiness audit** — inspect application, security, database, deployment, secrets, monitoring, DR, providers, billing, Agent governance, tenant isolation and customer UX/support readiness.
2. **Blocker register** — classify every finding as 🔴 Blocker, 🟠 Required before launch, 🟡 Launch follow-up, or 🟢 Ready/evidenced.
3. **Production target** — provision and harden the actual target; record infrastructure identity and configuration evidence.
4. **Exact release deployment** — deploy the certified release identity and preserve immutable deployment evidence.
5. **Security/network validation** — verify TLS, ingress/egress, firewall, secret lifecycle, credential rotation and relevant attack surfaces.
6. **Data protection** — validate backup integrity, restore procedure and migration/recovery behavior.
7. **DR measurement** — perform real recovery drills and record measured RPO/RTO.
8. **Observability** — measure SLI/SLO and error-budget behavior under representative production conditions.
9. **Provider validation** — validate intentionally configured live providers using production-safe credentials and record target-specific evidence.
10. **Tenant/RBAC acceptance** — validate Vendor → Reseller → Client isolation and authorization on the deployed target.
11. **Security testing** — authenticated DAST and independent security/pentest review; disposition findings.
12. **HA/failure recovery** — rehearse dependency/service failures and document recovery behavior.
13. **Operations** — verify alerting, escalation, staffed on-call and incident response.
14. **External acceptance** — complete Vendor, Reseller and Customer acceptance where applicable.
15. **Go-live decision** — reconcile all exceptions and explicitly authorize commercial publication.

### Commercial gate rule

`Engineering Ready ≠ Release Certified ≠ Production Deployed ≠ Commercially Accepted`

A passing repository certification is necessary but does not prove real deployment, live-provider behavior, measured SLO/DR, independent security review or customer acceptance.

## Stage 7 — External Production Certification & Customer Acceptance

**Issues:** #210 / #269 / #19 — **ACTIVE / EXTERNAL-PENDING**

| Priority | Work package | Status |
|---|---|---|
| P0 | Immutable release identity | `v1.4.2` published and exact-SHA certified |
| P0 | External production deployment | Pending real infrastructure |
| P0 | Backup/restore & DR | Pending target evidence and measured RPO/RTO |
| P0 | Production SLO/SLI | Engineering contract exists; target measurement pending |
| P0 | Live provider validation | Pending |
| P0 | Vendor → Reseller → Client isolation/RBAC | External evidence pending |
| P0 | DAST / independent security review | External evidence pending |
| P0 | Networking / TLS / secret lifecycle | Target evidence pending |
| P0 | HA/failure recovery | Target rehearsal pending |
| P0 | Incident response / on-call | Live drill pending |
| P0 | Final external certification / customer acceptance | Pending #210/#269 |

### Recommended production infrastructure

Canonical baseline: `docs/current/PRODUCTION_SERVER_BASELINE.md`.

- **Staging:** 4 vCPU / 8 GB RAM / 100 GB SSD.
- **Initial production:** 8 vCPU / 16 GB RAM / 150–200 GB NVMe/SSD.
- **Growth:** 12–16 vCPU / 32 GB RAM / 250 GB+ NVMe/SSD.
- Ubuntu 24.04 LTS, fixed/public IP, TLS ingress, hardened firewall, encrypted off-host backups and centralized observability.
- Kubernetes is not required for the first external target; a hardened Docker-based deployment is sufficient when recovery and security controls are verified.
- GPU is optional for remote-provider inference and mainly relevant to local model inference/GPU OCR.

These sizing values are recommendations, not evidence that infrastructure has been provisioned.

## Stage 8 — AI Company Operating Model Foundation

**Class:** PRODUCT / ARCHITECTURE — **GOVERNED WORKFORCE FOUNDATION IMPLEMENTED; ACCEPTANCE/EVIDENCE RECONCILIATION WHERE REQUIRED; NOT A RELEASE IDENTITY**

The governed workforce foundation is the substrate for Stage 9. PR #514 connected policy decisions to the audit bridge, PR #516 implemented governed AgentInstance replacement, and PR #517 preserved AgentInstance principal identity through workflow child runs.

Do not reimplement these foundations merely because older audit documents still describe them as gaps. Reconcile remaining acceptance/evidence criteria against current code and tests.

## Stage 9 — Autonomous Workforce Optimization

**Class:** PRODUCT / ENGINEERING — **CURRENT PLANNED SLICES IMPLEMENTED AND RELEASE-CERTIFIED IN `v1.4.2`**

The certified Stage 9 scope is:

1. capability-aware workload routing;
2. task/risk/cost-aware model selection;
3. queue-aware workload balancing;
4. persisted workload-balancing evidence;
5. telemetry-backed Agent fitness;
6. Agent version fitness;
7. promotion evidence;
8. governed promotion;
9. governed rollback planning;
10. workforce capacity forecasting;
11. governed workforce scaling.

The control architecture is deliberately bounded:

`Forecast / Evidence → Governed Proposal → Existing Governance → Provision / Access Review / Activation`

Optimization cannot directly bypass identity, policy, approval, budget, lifecycle, concurrency, audit or execution controls.

### Stage 9 certification checkpoint

- Release: `v1.4.2`
- Exact SHA: `dba0bb672deb1236b6724bb8851526e656f47967`
- Production Certification Run: `35108008066`
- Certification Job: `104834133092`
- Product Gate Failures: **0**
- Evidence artifact: `production-certification-evidence-v1.4.2-dba0bb672deb1236b6724bb8851526e656f47967`
- Artifact ID: `10450993330`

A non-gating fixture-cleanup DBAPIError was observed in Tenant/RBAC certification logs. It did not produce a Product Gate failure and did not change the PASS result.

## Stage 10 — AI Company Operating System

Long-term product vision: organization-wide command, policy-governed autonomy, agent/version registry, workforce analytics, orchestration and tenant-safe operations. This is not a current implementation claim.

## Cross-cutting Definition of Done

Every stage must preserve tenant isolation, RBAC, equivalent Human/Agent authorization, policy-driven approvals, scoped credentials, auditable identity, safe test execution, secret exclusion, one authoritative Alembic graph, reproducible CI/release artifacts, explicit evidence boundaries and documentation reconciliation.

## Evidence boundary

Repository tests, PR CI, CodeQL, local Docker, production-like validation, synthetic load and simulated providers are engineering/release evidence only. They do not substitute for live production deployment, measured production SLO/DR, independent security review or customer acceptance.

Certification never transfers automatically across SHAs.

## Canonical companion records

- `docs/00_START_HERE/VERSIONING_TRUTH.md`
- `docs/00_START_HERE/CURRENT_STATUS.md`
- `docs/00_START_HERE/CURRENT_PRIORITIES.md`
- `docs/current/PRODUCTION_SERVER_BASELINE.md`
- `docs/current/PRODUCTION_EVIDENCE_INDEX.md`
- `docs/current/PRODUCTION_CERTIFICATION_EXECUTION_PACK.md`
- `docs/current/STAGE_8_IMPLEMENTATION_STATUS.md`
- `docs/current/STAGE_9_IMPLEMENTATION_STATUS.md`
- `docs/engineering/STAGE_8_GOVERNANCE_AUDIT_CHECKLIST.md`
- `docs/blueprint/STAGE_8_ENGINEERING_EXECUTION_PLAN.md`
- `docs/releases/RELEASE_TRUTH_LEDGER.md`
