# Versioning Truth

**Status:** CANONICAL
**Reconciled:** 2026-10-07

This document defines the independent version axes used by the AI Employee Platform.

## 1. Release version

A **Release** is an immutable product snapshot identified by a Git tag and exact commit SHA. Certification, deployment evidence, customer acceptance and rollback evidence attach to that exact SHA.

### Current release truth

- Latest published release: **`v1.4.17`**
- Latest exact-SHA certified release: **`v1.4.17`** at `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
- `v1.4.17` Git tag: **VERIFIED**, resolving to the certified release commit.
- `v1.4.17` GitHub Release: **PUBLISHED**, not draft, not prerelease.
- `v1.4.17` exact-SHA Production Certification: **PASS** on run `37625345534`, job `112805570856`.
- Evidence artifact: `production-certification-evidence-v1.4.17-b403c0dcdea579e017738a6fdea138c2b1a2999c`.
- Evidence digest: `sha256:c05d9ba79e135dfb64ffd7aed89e2fd36b1ebcb53f6ef2ddfb865e516b870e3d`
- External production deployment: **NOT VERIFIED / not claimed**.
- Customer acceptance / live provider validation / realized revenue: **NOT VERIFIED**.

`v1.4.17` is the current immutable engineering/release-certified snapshot. It must not be described as externally production-verified until target-specific evidence exists.

Current `main` contains documentation and other post-release engineering history. The exact current Git HEAD is authoritative and must be resolved directly from Git metadata. Documentation commits after `v1.4.17` do not inherit its certification.

## 2026-10-07 v1.4.17 publication truth

- Release: **v1.4.17**
- Exact certified SHA: **b403c0dcdea579e017738a6fdea138c2b1a2999c**
- Certification Run: **37625345534**
- Certification Job: **112805570856**
- Result: **PASS**
- Product Gate failures: **0**
- Git tag: **VERIFIED**
- GitHub Release: **PUBLISHED**
- Production deployment: **NOT VERIFIED / NOT CLAIMED**
- Customer acceptance/revenue: **NOT VERIFIED**

Certification is bound only to the exact immutable release SHA. Publication did not create new application-code certification.

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

Stage 9 is the optimization layer above the governed execution substrate. Its current planned slices were implemented and certified as part of the v1.4.2 release and remain included in the current v1.4.17 release:

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
- Merge SHA: `1ded1b9d33056eaf21806208aba1bebebb9fb2d8`.
- Dedicated real-stack E2E Run `37308738607` — **PASS**.
- Verification head: `fe6377abcc7f110aa83a8cff3b8a0ea7e5c10c99`.
- W20 lifecycle/install/revoke/audit and governed marketplace mechanics are **REAL-STACK VERIFIED**.
- Provider execution, external marketplace revenue, seller payout, tax settlement, production deployment and customer acceptance remain **NOT VERIFIED**.
- Exact-SHA Production Certification: **NOT RUN**.
- Any release containing W20 application code requires fresh exact-SHA certification.



## W21 versioning boundary — 2026-10-05

W21 AI Business Network is **IMPLEMENTED / REAL-STACK VERIFIED** on post-v1.4.16 mainline.

- PR #909; merge SHA `b6f9efdf067fdef5b9c6fad65002ee34998e5545`.
- Dedicated E2E Run `37314768222` — PASS; CI/security/production-like gates passed.
- W21 is not a release version and does not inherit v1.4.16 certification.
- Exact-SHA Production Certification: **NOT RUN**.
- External network execution, contractual commitment, financial settlement, production deployment and customer acceptance remain **NOT VERIFIED**.
- Any future release containing W21 requires fresh exact-SHA certification.


## 18. W22 SEO & Growth Employee — verified

W22 is post-v1.4.16 mainline engineering and is not a release version.

- Issue #910; PR #911; merge SHA `a4d828045ec4cc299a796edafd53eb3a79c7186d`.
- Dedicated W22 real-stack E2E Run `37320308304` — **PASS**.
- CI/security/production-like gates on the verification head passed.
- Live search-engine execution, ranking/traffic impact, production deployment, customer acceptance and exact-SHA Production Certification remain **NOT VERIFIED / NOT RUN**.
- Any future release containing W22 requires fresh exact-SHA certification.

## 19. W23 Customer Success & Support Employee

W23 is post-v1.4.16 mainline engineering and is not a release version.

- Issue #912; PR #913; merge SHA `9c391bc19a4bd97c38a1c2181918bde0a4a6b5b0`.
- Dedicated W23 real-stack E2E Run `37321108385` — **PASS**.
- CI/security/production-like gates passed on the verification head.
- Live inbox/provider execution, customer outcome impact, production deployment, customer acceptance and exact-SHA Production Certification remain **NOT VERIFIED / NOT RUN**.
- Any future release containing W23 requires fresh exact-SHA certification.

## 20. W10 customer-outcome / revenue-event evidence

W10 Issue #914 / PR #915 is post-v1.4.16 mainline engineering.

- Merge SHA: `ecab2c23fd945b04ef82c2f21dfb6f76ca74b082`.
- Verification head: `fa57a72f2379fb43d4dcc4a6acb7b33b955d479d`.
- Dedicated E2E Run `37326882407` — PASS.
- CI/security/production-like gates passed on the verification head.
- Verified mechanics: governed proposal/pilot deal, payment correlation, order settlement, revenue-event ledger creation and replay idempotency.
- Provider: deterministic `contract-test`; real customer payment/revenue remains NOT VERIFIED.
- Exact-SHA Production Certification: NOT RUN.
