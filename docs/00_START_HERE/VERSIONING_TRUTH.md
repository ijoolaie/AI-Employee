# Versioning Truth

**Status:** CANONICAL
**Reconciled:** 2026-10-05

This document defines the independent version axes used by the AI Employee Platform.

## 1. Release version

A **Release** is an immutable product snapshot identified by a Git tag and exact commit SHA. Certification, deployment evidence, customer acceptance and rollback evidence attach to that exact SHA.

### Current release truth

- Latest published release: **`v1.4.16`**
- Latest certified release: **`v1.4.16`**, exact certified SHA `434a0c4a4501af08a393faaf58092add764df2a2`.
- `v1.4.16` Git tag: **VERIFIED**, resolving to the certified release commit.
- `v1.4.16` GitHub Release: **PUBLISHED**, not draft, not prerelease.
- `v1.4.16` exact-SHA Production Certification: **PASS** on run `37188879277`, job `111396657270`.
- Evidence artifact: `production-certification-evidence-v1.4.16-434a0c4a4501af08a393faaf58092add764df2a2`.
- Evidence digest: `sha256:7af4640395aefcffe0485fc3b276dad0dc794a97333efe59d531ef8af74d3d70`
- External production deployment: **NOT VERIFIED / not claimed by certification**.
- Customer acceptance / live provider validation: **PENDING**.

`v1.4.16` is the current engineering/release-certified snapshot. It must not be described as externally production-certified until target-specific evidence exists.

Current `main` contains post-v1.4.16 engineering work. The W13 candidate SHA has fresh exact-SHA certification evidence, but certification does not create a Git tag or release. The exact current Git HEAD is the authoritative engineering head and must be resolved directly from the repository rather than copied into this document. A new application-code release candidate must receive fresh exact-SHA certification.

## 2. Architecture version

An **Architecture Version** describes the intended platform architecture and operating model. It is not a release identity unless an explicit release record says so.

### Architecture truth

- **V1.4:** frozen architecture foundation.
- **V1.5:** active Agentic Operating Model extension.

V1.5 is an architecture/operating-model baseline, not a separately certified release. It defines the Human + Agent model and governance contracts; implementation claims require code and test evidence.

Canonical architecture document:
`docs/blueprint/V1.5_AGENTIC_OPERATING_MODEL.md`

## 3. Engineering phase

An **Engineering Phase** records implementation work and acceptance gates. Phases are not release numbers.

Current phase truth:

- Phase 11 Unified Execution acceptance: **COMPLETE**
- Phase 12 Test Center: **IMPLEMENTED / OPERATIONAL HARDENING**
- Phase 13 Agent Teams & Marketplace: **ENGINEERING COMPLETE**
- Phase 14.1–14.16: **ENGINEERING COMPLETE WHERE TRACKED**
- Stage 7: **ACTIVE — EXTERNAL PRODUCTION EXECUTION / CERTIFICATION PENDING EXTERNAL TARGET**
- Stage 8: **GOVERNED AGENT WORKFORCE FOUNDATION IMPLEMENTED; ACCEPTANCE/EVIDENCE RECONCILIATION CONTINUES WHERE REQUIRED**
- Stage 9: **CURRENT PLANNED SLICES IMPLEMENTED; PRESENT IN THE CURRENT v1.4.11 RELEASE**

## 4. Stage 9 optimization workstream

Stage 9 is the optimization layer above the governed execution substrate. Its current planned slices were implemented and certified as part of the v1.4.2 release and remain included in the current v1.4.11 release:

1. Capability-aware workload routing.
2. Task/risk/cost-aware model selection.
3. Queue-aware workload balancing.
4. Persisted workload-balancing evidence.
5. Telemetry-backed Agent fitness.
6. Agent version fitness.
7. Promotion evidence.
8. Governed promotion.
9. Governed rollback planning.
10. Workforce capacity forecasting.
11. Governed workforce scaling control loop.

Optimization remains subordinate to identity, policy, approval, budget, lifecycle, concurrency, audit and execution controls.

## 5. Agent capability workstream

The focused Agent capability gate remains separate from external production deployment. The capabilities are:

1. **Tool Calling** — model/tool execution contract, allow-listed registry and execution guardrails.
2. **Structured Arguments** — JSON-schema-defined arguments, provider-neutral validation and fail-closed behavior before side effects.
3. **Multi-step** — bounded model → tool → result → model cycles with explicit iteration/step limits and auditability.
4. **Provider validation** — real-provider validation, starting with LM Studio.
5. **Release gate** — fresh exact-SHA certification for Agent capability code promoted into a release.

These capabilities are substantially present in the architecture; active work should focus on acceptance evidence and hardening rather than rebuilding the stack from zero.

## 6. How the axes relate

```text
RELEASE
v1.3.8 ─────► v1.4.2 ─────► v1.4.5 ─────► v1.4.6 ─────► v1.4.7 ─────► v1.4.8 ─────► v1.4.9 ─────► v1.4.10 ─────► v1.4.12
 historical     certified      historical certified                 current certified
                                                             |
                                                             +-- external production: pending

ARCHITECTURE
V1.4 frozen foundation
        │
        ▼
V1.5 Agentic Operating Model

ENGINEERING
Phase 11 → 12 → 13 → 14.x → Stage 7 external execution
                              └→ Stage 8 governed workforce foundation
                                  └→ Stage 9 optimization/control loops
```

These axes may advance independently.

## 7. Evidence rules

1. A blueprint does not prove implementation.
2. An engineering phase does not create a release.
3. A release tag does not prove external production deployment.
4. CI/browser/production-like evidence does not prove customer acceptance.
5. Certification evidence is bound to the exact commit SHA.
6. No evidence transfers automatically across SHAs.
7. Historical documents remain traceable but cannot override current canonical truth.

## 8. Naming rule

- `vX.Y.Z` → immutable product release.
- `VX.Y` → architecture baseline/generation.
- `Phase N` → engineering workstream/gate.
- `Stage N` → program/product stage.
- `RC` → release candidate.
- `CERTIFIED` → exact-SHA certification evidence exists.
- `PRODUCTION VERIFIED` → independently verified deployment evidence exists.

## 9. Source-of-truth order

For release truth:
1. `docs/releases/RELEASE_TRUTH_LEDGER.md`
2. exact Git tag and commit SHA
3. certification/deployment evidence

For architecture truth:
1. canonical blueprint documents
2. `docs/00_START_HERE/PROJECT_OVERVIEW.md`
3. implementation traceability

For engineering status:
1. `docs/00_START_HERE/CURRENT_STATUS.md`
2. `docs/current/PRODUCTIZATION_ROADMAP.md`
3. phase-specific evidence
4. verified CI/test evidence

If documents disagree, update the canonical document rather than creating a parallel status file.


## 10. W11 identity/presentation boundary

W11 Humanized Employee Identity & Visual Presentation is post-v1.4.11 mainline engineering. Its initial slice adds stable avatar metadata to the Employee identity model; it is not part of the immutable v1.4.11 release and has no transferred certification evidence. A release containing W11 application code requires fresh exact-SHA certification.

## 11. Virtual AI Company / Presentation-Commerce boundary

The post-v1.4.11 roadmap now includes a Presentation Layer for a visual AI Company Headquarters.

Planned sequence:
W11 Humanized Employee Identity → W12 Virtual Office → W13 Customer HQ Progression → W14 Employee Appearance → W15 Wardrobe/Cosmetics → W16 Skills Marketplace → W17 Career/Reputation → W18 Virtual Meetings → W19 Voice/Visual → W20 Third-party Employee Marketplace → W21 AI Business Network.

These are engineering/product phases, not release numbers. The Presentation Layer remains downstream of Workforce Core truth: Employee / WorkItem / Run / Governance / Approval / Audit / Metrics → Presentation.

No visual state, cosmetic purchase, marketplace asset or avatar provider creates execution authority. Any application-code phase promoted into a release requires fresh exact-SHA certification.

## 12. W12 Virtual Office implementation boundary

W12 now contains a first post-v1.4.11 implementation slice: a tenant-scoped read-only office-state API and customer Virtual Office UI. The implementation derives presentation state from existing Employee/Run/WorkflowApproval data and does not introduce a second execution state store or authorization path.

W12 is not part of immutable `v1.4.11`. Exact-SHA certification must cover any future release containing W12 code.



## 13. v1.4.12 release

- Published release: `v1.4.12`.
- Exact certified SHA: `9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519`.
- Production Certification: Run `37138840482`, Job `111248877948` — PASS.
- Immutable certification evidence artifact: `production-certification-evidence-v1.4.12-rc.1-9c3f0ff7dc8fffcce8e069e18b11cf13d4dc0519` with digest `sha256:b380f8849b6347995c17bcec8a97de979b2a67b01d88dc26d0f02258b8779af1`.
- Production deployment remains **NOT VERIFIED**.
- External customer acceptance and revenue remain **NOT VERIFIED**.

W12 Virtual Office is therefore part of the immutable v1.4.12 release boundary. Any subsequent W13+ application-code work is post-release mainline and requires fresh exact-SHA certification before promotion.

## 14. v1.4.13 candidate certification — 2026-10-03

- Candidate scope: W13 Customer HQ Progression.
- Exact certified candidate SHA: `5d57d9929cc5e924c5b9147dc0b0a41d25f39d83`.
- Production Certification: Run `37141161822`, Job `111255715821` — **PASS**.
- Evidence artifact: `production-certification-evidence-v1.4.13-rc.1-5d57d9929cc5e924c5b9147dc0b0a41d25f39d83`.
- Evidence digest: `sha256:35e4b5dea1c57a3c021051f4dacaa841dee2f6c17cea9f0ed5db505676ea9479`.
- Production deployment: **NOT VERIFIED**; certification explicitly records `production_deployment_claimed:false`.
- Git tag/release: **NOT CREATED** at reconciliation time.

Certification is complete for the exact candidate SHA. Manual tag/release promotion is the remaining release step; no certification transfers to later SHAs.

## 15. W16 post-v1.4.16 evidence reconciliation

W16 Skills Marketplace is no longer merely planned. The current mainline contains lifecycle, employee Skill API, publication/discovery, governed provider execution, cross-tenant purchase/settlement, financial allocation/reporting, payout proposal/destination controls and approval-gated deterministic payout execution evidence.

These are **post-v1.4.16 engineering evidence** and do not extend the immutable v1.4.16 certification. External marketplace payment/revenue, external seller payout, tax settlement and production deployment remain **NOT VERIFIED**.

## 16. W17 Employee Career & Reputation

W17 is the active next product-experience slice as of 2026-10-05.

- Issue: #897.
- Status: **IMPLEMENTED / REAL-STACK VERIFIED**.
- Contract: `docs/current/W17_EMPLOYEE_CAREER_REPUTATION.md`.
- Scope: evidence-first career history, tenure, verified operational indicators and evidence-backed achievements.
- Hard boundary: no fabricated metrics, no opaque reputation score, no authority changes.
- Release boundary: post-v1.4.16; fresh exact-SHA certification is mandatory before any release promotion.


## W17 versioning boundary — 2026-10-05

W17 Employee Career & Reputation is post-v1.4.16 mainline engineering.

- Implementation integration commit: `e857528167e826b335a6448cce4b5ad3240a4d46`.
- Dedicated real-stack E2E harness/workflow is present in main.
- W17 is **not** a release version and does not modify the certified v1.4.16 artifact.
- Dedicated real-stack E2E: Run `37298325542`, Job `111724800314` — **PASS**.
- CodeQL on the verification head: Run `37298325646` — **PASS**.
- Verification workflow reconciliation merged as `53e47d2031dfc00de1b32e8b4fc8f1be0073b139`.
- W17 is **IMPLEMENTED / REAL-STACK VERIFIED** on the post-v1.4.16 engineering mainline.
- Exact-SHA Production Certification, deployment, external provider execution and customer acceptance remain **NOT VERIFIED**.


## W18 verification boundary — 2026-10-05

W18 Virtual Meeting Rooms first vertical slice is **IMPLEMENTED / REAL-STACK VERIFIED** on post-v1.4.16 mainline.

- Integration merge: `a5fd482e456ba2060705aa24ff3f63de0e2a7665`.
- Verification head: `7ae4fe590d5483185637a8f344cc592979fec8bf`.
- Dedicated W18 E2E: Run `37299435745`, Job `111728381943` — **PASS**.
- CI and security/production-like checks passed on the same verification head.
- W18 is not a release version and does not inherit `v1.4.16` certification.
- Exact-SHA Production Certification, external deployment and customer acceptance remain **NOT VERIFIED**.

W19 is the next product-experience implementation slice.

## 17. W20 Third-party Employee Marketplace

W20 is post-v1.4.16 mainline engineering and is not a release version.

- PR: #907.
- First vertical slice: **IMPLEMENTED; REAL-STACK VERIFICATION PENDING**.
- Exact-SHA Production Certification: **NOT RUN**.
- External provider execution, marketplace revenue, payout and tax settlement: **NOT VERIFIED**.
- Any release containing W20 application code requires fresh exact-SHA certification.



## W21 versioning boundary — 2026-10-05

W21 AI Business Network is **IMPLEMENTED / REAL-STACK VERIFIED** on post-v1.4.16 mainline.

- PR #909; merge SHA `b6f9efdf067fdef5b9c6fad65002ee34998e5545`.
- Dedicated E2E Run `37314768222` — PASS; CI/security/production-like gates passed.
- W21 is not a release version and does not inherit v1.4.16 certification.
- Exact-SHA Production Certification: **NOT RUN**.
- External network execution, contractual commitment, financial settlement, production deployment and customer acceptance remain **NOT VERIFIED**.
- Any future release containing W21 requires fresh exact-SHA certification.
