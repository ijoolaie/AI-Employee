# AI Employee Platform — Productization & Delivery Roadmap

## Roadmap truth — 2026-09-23

Three axes remain independent:

- **Release:** `v1.4.11` at exact certified SHA `90dd5cbcfb0a372ee5d53b34f65868cd0acb181f`, certified by Production Certification Run `35848311037`.
- **Architecture:** `V1.5 Agentic Operating Model`.
- **Engineering:** Stage 7 external production execution, Stage 8 governed Agent workforce foundation, and Stage 9 optimization/control loops.

`v1.4.11` is the latest published exact-SHA certified release. Current `main` contains post-certification source and documentation changes after the certified release SHA; those changes are not automatically certified as a new release.

## Current position

Phase 11 Unified Execution is complete. Phase 12 Test Center is operationally hardened. Phase 13 Agent Teams & Marketplace is engineering complete. Phase 14.1–14.16 tracked engineering is complete/reconciled.

The project is now in a dedicated **Product Completeness → Commercial Readiness & External Production** sequence. The audited product-completeness gate is closed for the current scope and remains under regression watch; the default next work is external evidence, deployment, security and operational validation.

## Product Completeness Gate — added 2026-09-21

The product-completeness gate was completed for the audited scope before v1.4.11 certification. External production gates remain independent and open pending an external target.

### Product-completeness requirements — CLOSED FOR CURRENT AUDITED SCOPE

1. **Persian/English localization:** **DONE for the audited customer operational scope**; EN/FA browser acceptance, locale-aware formatting and true RTL direction coverage are in place.
2. **Customer Employee Templates:** **DONE for the audited scope**; the customer-facing curated catalog contains seven tenant-safe bilingual starter templates with lifecycle/installation metadata. These seven templates are the current **operational/customer starter catalog**, not the complete AI-company workforce role catalog.
3. **Operational lists and lifecycle:** **DONE for the audited scope**; Product, Customer, Order/Invoice and Schedule lifecycle parity uses resource-specific non-destructive semantics where retention/auditability requires them.
4. **Backend/frontend parity:** **DONE for the audited scope**; customer-visible lifecycle actions map to supported and authorized operations.
5. **Shared UX states:** **DONE for the audited scope**; customer Analytics/Reporting retry and empty states plus permission/lifecycle state handling are covered.
6. **Browser acceptance:** **DONE for the audited scope**; principal customer operational routes are accepted in both `en` and `fa`, including `lang`/`dir` assertions.
7. **Edition-aware Test Center — DONE:** Vendor, Reseller and Customer definition visibility and execution boundaries are edition-aware; shared isolation/RBAC/execution controls remain covered at the shared boundary, without requiring every service in every edition.

Canonical record: docs/current/PRODUCT_COMPLETENESS_GATE_2026-09-21.md.

This gate was the source-change gate completed before v1.4.11 certification. It does not modify or weaken immutable historical release certifications.

## Commercial Readiness Gate

### Objective

Prove that the certified product can be operated safely, observably and recoverably in a real production environment and can pass the required partner/customer acceptance gates.

### Required gate sequence

1. **Readiness audit** — inspect application, security, database, deployment, secrets, monitoring, DR, providers, billing, Agent governance, tenant isolation and customer UX/support readiness.
2. **Blocker register** — classify every finding as blocker, required-before-launch, follow-up, or ready/evidenced.
3. **Production target** — provision and harden the actual target; record infrastructure identity and configuration evidence.
4. **Exact release deployment** — deploy the accepted v1.4.11 release identity and preserve immutable deployment evidence.
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
| P0 | Immutable release identity | `v1.4.11` published and exact-SHA certified |
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

## Workforce role taxonomy — clarification

The product now distinguishes two related but different catalogs:

1. **Customer operational starter templates** — the current seven templates exposed by the Customer Employee Templates surface: Sales Assistant, Customer Support Agent, Order Assistant, Catalog Assistant, Report Analyst, Document Analyst and Finance Assistant.
2. **AI Company workforce role catalog** — the broader organizational workforce model defined in `docs/blueprint/AI_COMPANY_FOUNDING_WORKFORCE.md`. This includes executive/governance roles such as AI Chief of Staff and **AI Internal Manager**, plus domain managers and specialist roles.

The AI Internal Manager is a managerial workforce role. It supervises specialized AI employees and prepares governed proposals for CEO decisions covering hiring/provisioning, retirement/removal, transfer/reassignment, replacement, urgent operational budgets and financial estimates. Its authority is **CEO approval by default**, with explicit delegation available for routine, non-financial, non-critical and reversible operations. Delegation is scoped, auditable and revocable; financial, material-resource, security-sensitive, legal, production-critical and irreversible actions remain approval-gated.

The role model remains:

`Human CEO → AI Board → AI Chief of Staff → AI Internal Manager → Specialized AI Workforce`

The existing governed workforce substrate, proposal flow and CEO approval boundary remain the authoritative implementation path. Adding or activating these managerial roles is a separate workforce/product slice and must not be represented as already implemented merely because the architecture documents define them.

### Next requested workforce roles

The next workforce implementation slice is explicitly defined as:

1. **AI Marketing & Advertising Manager**
2. **AI Graphic Designer**
3. **AI Software Developer**
4. **AI Trader**

The first three may receive delegated routine operational authority within the CEO-defined scope. The AI Trader remains financial/high-impact and therefore requires explicit human approval for actual capital allocation or financial execution.

These roles are planned candidates, not a claim that active instances already exist in the current certified release.

## Stage 8 — AI Company Operating Model Foundation

**Class:** PRODUCT / ARCHITECTURE — **GOVERNED WORKFORCE FOUNDATION IMPLEMENTED; ACCEPTANCE/EVIDENCE RECONCILIATION WHERE REQUIRED; NOT A RELEASE IDENTITY**

The governed workforce foundation is the substrate for Stage 9. Do not reimplement these foundations merely because older audit documents still describe them as gaps. Reconcile remaining acceptance/evidence criteria against current code and tests.

## Stage 9 — Autonomous Workforce Optimization

**Class:** PRODUCT / ENGINEERING — **CURRENT PLANNED SLICES IMPLEMENTED; PRESENT IN v1.4.11**

The planned Stage 9 slices were implemented and exact-SHA certified in v1.4.2 and remain part of the current v1.4.11 release:

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
