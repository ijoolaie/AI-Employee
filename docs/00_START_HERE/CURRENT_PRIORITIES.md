# Current Priorities

**Reconciled:** 2026-09-16
**Latest published release:** `v1.4.2`
**Release SHA:** `dba0bb672deb1236b6724bb8851526e656f47967`
**Production Certification:** Run `35108008066` — PASS
**Current engineering mainline:** documentation reconciliation after certified `v1.4.2` SHA
**Current status:** STAGE 9 RELEASE-CERTIFIED / EXTERNAL PRODUCTION EXECUTION STILL PENDING

## Priority order

### P0 — External production boundary

1. Provision and verify the real production target.
2. Bind deployment to an immutable certified release SHA/tag.
3. Perform real backup/restore/DR and measure RPO/RTO.
4. Measure production SLO/SLI and error budget.
5. Validate live providers with production-safe credentials.
6. Certify Vendor → Reseller → Client isolation/RBAC on the deployed target.
7. Execute authenticated DAST where applicable.
8. Obtain independent security review / penetration-test evidence.
9. Verify production networking, TLS, egress and secret lifecycle.
10. Rehearse HA/failure recovery and incident response/on-call.
11. Complete ordered external certification and customer acceptance (#210/#269).

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
