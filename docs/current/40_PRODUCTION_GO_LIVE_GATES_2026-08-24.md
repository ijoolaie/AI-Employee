# Production / Commercial Go-Live Gates

**Status date:** 2026-08-24  
**Target release:** `v1.2.0`

## Gate A — Release artifact

- [x] Immutable release identity exists.
- [x] Runtime artifact exists.
- [x] Vendor/reseller/customer edition artifact exists.
- [x] Checksums recorded.
- [x] Release certification recorded.

## Gate B — External production target

- [ ] Production host/managed target provisioned.
- [ ] Protected GitHub `production` Environment configured.
- [ ] Least-privilege deployment identity configured.
- [ ] Production registry configured.
- [ ] Database configured.
- [ ] Redis/queue configured.
- [ ] HTTPS and trusted origins configured.
- [ ] Production secrets loaded through an approved secret manager.

## Gate C — Deployment execution

- [ ] Immutable v1.2.0 revision deployed.
- [ ] Database migration executed and migration heads recorded.
- [ ] API liveness/readiness PASS.
- [ ] Worker and Beat health PASS.
- [ ] Frontend entry points PASS.
- [ ] Queue processing PASS.

## Gate D — Observability and recovery

- [ ] External monitoring active.
- [ ] External alert delivery tested.
- [ ] Production backup created before migration.
- [ ] Target restore rehearsal PASS.
- [ ] Previous known-good release recorded.
- [ ] Rollback rehearsal PASS.

## Gate E — Commercial

- [ ] Payment provider configured if required by contract.
- [ ] Webhook signature verification tested.
- [ ] Subscription/licensing path tested.
- [ ] Real subscriber/payment evidence recorded.
- [ ] Customer acceptance smoke test PASS.
- [ ] Support/escalation owner recorded.

## Gate F — Security certification

- [ ] Production secrets verified absent from Git.
- [ ] HTTPS/TLS verified.
- [ ] CORS/trusted origins verified.
- [ ] Authentication/authorization smoke tests PASS.
- [ ] Rate limiting/fail-closed behavior verified.
- [ ] Production logs contain no secret material.
- [ ] Target-specific security review completed.

## Final decision rule

`v1.2.0` may be called **Production Certified** only when Gates A–F are complete with fresh evidence from the actual target. Local Docker production-like tests and GitHub Actions artifact creation are not substitutes for external production evidence.

Until then:

**Release:** CERTIFIED FOR CONTROLLED DEPLOYMENT  
**Production:** NOT CERTIFIED  
**Commercial Go-Live:** NOT CERTIFIED
