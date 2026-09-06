# Current Priorities

**Reconciled:** 2026-09-06  
**Certified release candidate:** `v1.3.8`  
**Certified commit:** `fd1e74b6b4c1701f7443efc202bad161ff19618c`

## Executive priority

Application engineering and the production-like certification gate are complete for `v1.3.8`. The immediate priority is now **real production infrastructure**, followed by controlled deployment of the frozen release identity.

The previous deployment attempt (`34060615390`) failed at SSH configuration because the production Environment inputs were empty/missing. No remote deployment occurred.

## P0 — external production gates

1. **Provision a real production target** — VPS/cloud host, network, storage and DNS.
2. **Configure protected production Environment inputs** — SSH key, host, user, app directory, production environment payload and known-hosts data.
3. **Deploy exact `v1.3.8` identity** — `fd1e74b6b4c1701f7443efc202bad161ff19618c`.
4. **Verify deployed identity and service health** — confirm release, commit, migrations and all required services.
5. **Real backup/restore & DR drill** — prove target RPO/RTO.
6. **Production SLO/SLI & error budget** — measure the deployed target.
7. **Live provider validation** — validate real AI/email/payment/storage/provider behavior and failure modes.
8. **Vendor → Reseller → Client runtime isolation/RBAC** — complete real-stack evidence for #19.
9. **DAST against deployed target** — authenticated scan, triage and retest.
10. **Independent penetration test/security review** — obtain independent findings and disposition.
11. **Production networking hardening** — prove TLS, ingress, firewall and network-policy evidence.
12. **Secret management, rotation & recovery** — prove the external lifecycle.
13. **HA/failure-recovery rehearsal** — rehearse target failure/failover against objectives.
14. **Incident-response drill and on-call** — prove alert ownership, escalation and response.
15. **Final external certification & customer acceptance** — reconcile all evidence to the exact release identity (#210/#269).

## P1 — productization / operational completeness

The previously tracked P1 engineering gates remain implemented/complete. Target-environment verification is now the main remaining boundary where applicable.

## Certified release checkpoint

- Release: `v1.3.8`
- Tag target: `fd1e74b6b4c1701f7443efc202bad161ff19618c`
- Certification: Run `34052885700` — PASS
- Marketplace critical Playwright flow: PASS
- Deployment attempt: Run `34060615390` — failed at SSH setup before remote deployment
- Deployment checkpoint: Issue #343

## Evidence rules

- CI/internal validation = engineering/release evidence.
- Production-like certification = certified release-candidate evidence.
- Real production deployment = target evidence.
- Customer acceptance = independent acceptance evidence.
- Certification never transfers automatically across SHAs.
- Never fabricate production configuration, credentials, provider evidence or compliance certification.
- Never place secrets in GitHub issues, commits, documentation or chat.
