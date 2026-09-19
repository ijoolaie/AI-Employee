# Current Priorities

**Reconciled:** 2026-09-19
**Latest published release:** `v1.4.5`
**Release SHA:** `dba0bb672deb1236b6724bb8851526e656f47967`
**Production Certification:** Run `35108008066` — PASS
**Current status:** v1.4.5 ENGINEERING-VALIDATED / EXTERNAL PRODUCTION & COMMERCIAL ACCEPTANCE PENDING / COMMERCIAL READINESS & EXTERNAL PRODUCTION EXECUTION PENDING

## Current engineering baseline

- v1.4.5 release: `cc94bc9536f4f95680bb7a183313914c116ffcf2`
- release branch: `main`
- Exact release SHA: `cc94bc9536f4f95680bb7a183313914c116ffcf2`
- release GitHub Actions engineering validation: **10/10 release-critical workflows PASS**
- Local production-like certification: **PASS_ENGINEERING_EVIDENCE_EXTERNAL_PENDING**
- Latest published release: `v1.4.5`
- Certification evidence does not transfer between these SHAs.

## Priority order

### P0 — release freeze and external production readiness

1. Preserve the exact release SHA and release evidence.
2. Do not merge or retag until the final release identity is explicitly approved.
3. If external deployment is authorized, provision the approved target and capture immutable deployment identity.
4. Execute security/network/secret lifecycle validation.
5. Execute backup/restore and measure RPO/RTO.
6. Establish production SLI/SLO/error-budget measurements.
7. Validate live providers.
8. Certify Vendor → Reseller → Client isolation/RBAC on the deployed target.
9. Run authenticated DAST and independent security review.
10. Rehearse HA/failure recovery and incident response/on-call.
11. Complete Vendor/Reseller/Customer acceptance.
12. Reconcile residual risks and run the final commercial go-live gate.

### Evidence rules

- CI/internal validation = engineering evidence.
- Exact-SHA certification = release evidence.
- Real deployment = target evidence.
- Provider validation = environment/provider evidence.
- Security testing = security evidence.
- DR/restore rehearsal = resilience evidence.
- Customer acceptance = independent acceptance evidence.
- No evidence transfers automatically across SHAs.
- Documentation cannot substitute for missing operational evidence.
- Never fabricate infrastructure, provider, security, DR or acceptance evidence.

Broad feature expansion should remain paused unless the readiness audit identifies a genuine launch-blocking product requirement.
