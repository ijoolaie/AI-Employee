# Current Priorities

**Reconciled:** 2026-09-16
**Latest published release:** `v1.4.2`
**Release SHA:** `dba0bb672deb1236b6724bb8851526e656f47967`
**Production Certification:** Run `35108008066` — PASS
**Current engineering mainline:** documentation reconciliation after certified `v1.4.2` SHA
**Current status:** STAGE 9 RELEASE-CERTIFIED / COMMERCIAL READINESS & EXTERNAL PRODUCTION EXECUTION PENDING

## Priority order

### P0 — Commercial Readiness & External Production

The engineering/product core is release-certified in `v1.4.2`. The next phase is no longer primarily feature development; it is proving that the certified product can operate safely and acceptably in a real production environment.

Commercial publication must be treated as a gated sequence, not as an assumption based on CI alone:

1. **Production target** — provision the real production environment and record its immutable deployment identity.
2. **Certified release deployment** — deploy exactly the certified `v1.4.2` release / SHA and preserve deployment evidence.
3. **Security & networking** — verify TLS, firewall, ingress/egress policy, secret-manager lifecycle, credential rotation and production network boundaries.
4. **Database & data protection** — validate migrations, encrypted off-host backups, restore procedure and backup integrity.
5. **Disaster recovery** — execute restore/failure drills and measure actual RPO/RTO rather than relying on design documentation.
6. **Production observability** — define and measure SLI/SLOs, alerting and error-budget behavior against the deployed service.
7. **Live provider validation** — validate only intentionally configured production providers with production-safe credentials; record provider-specific evidence.
8. **Tenant isolation / RBAC** — certify Vendor → Reseller → Client isolation and authorization behavior on the deployed target.
9. **Authenticated DAST** — run applicable authenticated dynamic security testing against the production-like target and disposition findings.
10. **Independent security review** — obtain penetration-test / independent security-review evidence and record remediation or accepted exceptions.
11. **HA & failure recovery** — rehearse service, database, queue and dependency failures and document recovery behavior.
12. **Incident response / on-call** — verify operational ownership, alert routing, escalation and incident-response procedures.
13. **External acceptance** — complete the required Vendor, Reseller and Customer acceptance evidence where applicable.
14. **Commercial launch gate** — only after the above evidence is complete, reconcile exceptions/risks and explicitly authorize commercial go-live.

### P0.1 — Commercial readiness audit

Before spending effort on new product features, run a structured readiness audit across:

- application/backend correctness;
- frontend/customer UX;
- authentication, authorization and tenant isolation;
- database schema, migrations, backups and restore;
- deployment and infrastructure;
- secrets and credential lifecycle;
- monitoring, logging, alerting and SLOs;
- disaster recovery and business continuity;
- external providers and payment/integration paths;
- billing and commercial flows;
- Agent governance and execution controls;
- security testing and dependency exposure;
- Vendor / Reseller / Client operational boundaries;
- customer acceptance and support readiness.

Every finding must be classified as one of:

- **🔴 Blocker** — prevents external production/commercial launch.
- **🟠 Required before launch** — not necessarily a code defect, but evidence or operational work must be completed before launch.
- **🟡 Launch follow-up** — acceptable only if explicitly owned, bounded and documented.
- **🟢 Ready / evidenced** — requirement has current evidence tied to the relevant release/target.

The audit must distinguish **code readiness**, **release certification**, **target/deployment evidence**, and **customer acceptance**. These are separate evidence classes.

### P1 — Stage 9 optimization and governed control loops

Stage 9 implementation is complete for the current planned slices and is included in certified release `v1.4.2`.

Completed slices:

- capability-aware workload routing;
- task/risk/cost-aware model selection;
- queue-aware workload balancing;
- persisted workload-balancing evidence;
- telemetry-backed Agent fitness;
- Agent version fitness;
- promotion evidence;
- governed promotion;
- governed rollback planning;
- workforce capacity forecasting;
- governed workforce scaling control loop.

The optimizer remains subordinate to the governed execution substrate. It cannot bypass identity, policy, approval, budget, lifecycle, concurrency, audit or execution controls.

### P1.5 — Agent capability acceptance

The runtime already contains the core mechanics for tool calling, structured tool schemas/arguments and bounded multi-step execution. Do not reimplement these capabilities unnecessarily.

1. **Tool Calling** — prove provider-neutral model → tool → result → final-answer flow and allow-list enforcement.
2. **Structured Arguments** — validate JSON Schema before side effects; reject unknown tools, malformed IDs, non-object arguments, missing required fields, extra fields and wrong types.
3. **Multi-step** — prove sequential Tool A → Tool B → final answer, with hard iteration/step bounds and loop safety.
4. **Provider validation** — exercise LM Studio first; validate cloud providers only when intentionally configured.
5. **Release gate** — any future Agent capability code change requires fresh exact-SHA CI/certification.

### P2 — Next optimization evolution

The next Stage 9 increments should be driven by measured evidence rather than speculative rebuilds. Candidate work may include deeper provider/model telemetry, richer optimization feedback, and additional bounded control loops, while preserving human governance above the optimizer.

## Commercial publication rule

**Current conclusion:** `v1.4.2` is engineering/release-certified, but the project is **not yet externally production-certified for unrestricted commercial go-live**.

Do not describe the product as commercially production-ready solely because:

- CI passes;
- unit/integration/E2E tests pass;
- production certification passes;
- a Git tag/release exists;
- packages and checksums exist; or
- the application runs locally/in Docker.

Commercial go-live requires evidence from the real or approved production-like target for deployment, security, providers, observability, DR/RPO/RTO, operational recovery and acceptance. The repository certification is necessary evidence, but it does not substitute for external operational evidence.

### Current evidence boundary

| Evidence class | Current state |
|---|---|
| Backend / frontend / database engineering | Release-certified |
| Multi-tenancy / RBAC / Agent governance | Release-certified |
| Workflow / billing / WorkItem core flows | Release-certified |
| Stage 9 governed optimization | Release-certified |
| Exact-SHA production-like certification | PASS for `v1.4.2` |
| Real production deployment | Pending |
| Live provider validation | Pending / target-specific |
| Production SLO/SLI and error budget | Pending |
| Measured backup restore / DR RPO/RTO | Pending |
| Production networking / secret lifecycle | Pending |
| Authenticated DAST | Pending |
| Independent pentest / security review | Pending |
| HA / failure-recovery rehearsal | Pending |
| Staffed incident response / on-call | Pending |
| Vendor / Reseller / Customer acceptance | Pending |
| Final commercial go-live authorization | Pending |

## Infrastructure baseline

Use `docs/current/PRODUCTION_SERVER_BASELINE.md` as the canonical host/deployment sizing reference:

- staging: 4 vCPU / 8 GB / 100 GB;
- recommended initial production: 8 vCPU / 16 GB / 150–200 GB NVMe/SSD;
- growth tier: 12–16 vCPU / 32 GB / 250 GB+;
- Ubuntu 24.04 LTS;
- fixed/public IP, TLS ingress, hardened firewall;
- encrypted off-host backups;
- centralized monitoring and alerting.

These are recommendations, not evidence of a provisioned server.

## Evidence rules

- CI/internal validation = engineering evidence.
- Exact-SHA Production Certification = release evidence.
- Real deployment = target evidence.
- Provider validation = environment/provider evidence.
- Security testing = security evidence.
- DR/restore rehearsal = resilience evidence.
- Customer acceptance = independent acceptance evidence.
- No evidence transfers automatically across SHAs.
- Documentation cannot substitute for missing operational evidence.
- Never fabricate infrastructure, provider, security, DR or acceptance evidence.
- Any exception carried into launch must have an owner, scope, rationale, mitigation and explicit disposition.

## Next execution sequence

1. Create the Commercial Readiness audit and blocker register.
2. Resolve 🔴 blockers first; then complete 🟠 launch requirements.
3. Provision the real production-like target.
4. Deploy the exact certified release and capture immutable evidence.
5. Execute security, provider, observability, backup/restore, DR and failure-recovery validation.
6. Complete external acceptance evidence.
7. Reconcile the evidence ledger and outstanding exceptions.
8. Run the final commercial go-live gate.

Do not return to broad feature expansion until the readiness audit identifies a genuine product requirement that blocks launch.
