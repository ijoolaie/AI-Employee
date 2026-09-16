# Current Priorities

**Reconciled:** 2026-09-16
**Latest published release:** `v1.4.1`
**Release SHA:** `f7f5062feb125c7ca50263f74a0e40bc4abfa591`
**Certification run:** `34696339261` — SUCCESS
**Current engineering mainline:** `1c8c3ee2fc933148f90e967e18167fe602d0ad00`
**Current status:** STAGE 8 GOVERNANCE/EVIDENCE HARDENING + EXTERNAL PRODUCTION EXECUTION

## Priority order

### P0 — External production boundary

1. Provision and verify the real production target.
2. Bind deployment to an immutable release SHA/tag.
3. Perform real backup/restore/DR and measure RPO/RTO.
4. Measure production SLO/SLI and error budget.
5. Validate live providers with production-safe credentials.
6. Certify Vendor → Reseller → Client isolation/RBAC on the deployed target.
7. Execute authenticated DAST where applicable.
8. Obtain independent security review / penetration-test evidence.
9. Verify production networking, TLS, egress and secret lifecycle.
10. Rehearse HA/failure recovery and incident response/on-call.
11. Complete ordered external certification and customer acceptance (#210/#269).

### P1 — Stage 8 governance evidence

The governed Agent workforce foundation is implemented further than the older Stage 8 audit records indicated. PR #514 connected policy decisions to the audit bridge; PR #516 implemented governed AgentInstance replacement; PR #517 preserved AgentInstance identity through workflow child runs.

The remaining work is acceptance/evidence driven rather than a blanket rebuild:

1. Complete principal identity evidence for every protected agent execution path.
2. Complete tool allow-list, side-effect and approval-binding acceptance evidence.
3. Complete agent-to-agent trust acceptance tests and audit evidence.
4. Complete usage attribution, hard budget enforcement and runaway-execution acceptance evidence where gaps remain.
5. Reconcile each Stage 8 exit criterion to exact implementation files, tests and commit SHAs.
6. Run a fresh release-candidate certification before promoting Agent capability code into a release.

### P1.5 — Agent capability acceptance

The runtime already contains the core mechanics for tool calling, structured tool schemas/arguments and bounded multi-step execution. Do not reimplement these capabilities unnecessarily.

1. **Tool Calling** — prove provider-neutral model → tool → result → final-answer flow and allow-list enforcement.
2. **Structured Arguments** — validate JSON Schema before side effects; reject unknown tools, malformed IDs, non-object arguments, missing required fields, extra fields and wrong types.
3. **Multi-step** — prove sequential Tool A → Tool B → final answer, with hard iteration/step bounds and loop safety.
4. **Provider validation** — exercise LM Studio first; validate cloud providers only when intentionally configured.
5. **Release gate** — any code changes promoted into a release require fresh exact-SHA CI/certification.

### P2 — Stage 9 preparation

Do not treat Stage 9 as another pass of foundational CRUD/governance implementation. Its frontier is optimization above the now-governed execution substrate:

- capability-aware workload routing;
- task/risk/cost-aware model selection;
- measurable agent fitness/evaluation signals;
- version fitness, promotion and rollback evidence;
- predictive workforce capacity planning;
- governed autonomous scaling and rebalancing;
- optimization feedback loops with human governance above the optimizer.

Stage 9 should start only from gaps that remain after the Stage 8 exit audit, not from assumptions that already-implemented Stage 8 primitives are missing.

### Infrastructure baseline

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
- Customer acceptance = independent acceptance evidence.
- No evidence transfers automatically across SHAs.
- Never fabricate infrastructure, provider, security, DR or acceptance evidence.
