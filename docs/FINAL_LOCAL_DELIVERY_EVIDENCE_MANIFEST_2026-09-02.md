# AI-Employee Final Local Delivery Evidence Manifest

Date: 2026-09-02

## Release Identity

- Product release: v1.3.2 prerelease
- Canonical tested release SHA: 728b7f447d3bc6376fb01d47730cdd70eaf07746
- Candidate branch: release/v1.3.2-phase6e-candidate
- Migration head: p8_03_agent_binding
- Current repository HEAD: 7c3b9d5
- origin/main: bc51ac5

The canonical v1.3.2 certification identity remains the exact tested SHA above.
The current HEAD contains subsequent documentation/evidence commits and must not be represented as the original v1.3.2 certification identity.

## Previously Certified Release Evidence

- Phase 6E self-hosted rehearsal: PASS
- Production Certification: PASS
- Release packaging: PASS
- Workflow / approval / schedule product acceptance: PASS

Previously passing acceptance tests were not rerun because no invalidation condition occurred.

## Local Runtime Evidence

- Docker / Compose runtime: PASS
- PostgreSQL: Healthy
- Redis: Healthy
- API: Healthy
- Worker: Up
- Beat: Up
- API -> Redis DNS: PASS
- Worker -> Redis DNS: PASS
- Beat -> Redis DNS: PASS
- Redis PING: PASS
- Celery Beat scheduling: PASS
- API security-header smoke test: PASS

Evidence:
docs/LOCAL_RUNTIME_HARDENING_EVIDENCE_2026-09-02.md

## Disaster Recovery Evidence

- PostgreSQL custom-format backup: PASS
- Backup size: 227,279 bytes
- Backup SHA-256: DE6CB4A491092AE15B7047A50A1828910C1F6865C6428070BD33C4699411CFAC
- pg_restore --list: PASS
- TOC entries: 452
- Isolated restore: PASS
- Restored tables: 53
- Restored migration: p8_03_agent_binding
- Temporary restore database cleanup: PASS
- Main database modified during restore verification: NO
- PostgreSQL volume deleted: NO

Backup file is excluded from Git via:
artifacts/dr/

## Migration Evidence

- alembic current: p8_03_agent_binding
- alembic heads: p8_03_agent_binding
- Single migration head: PASS
- Migration upgrade/downgrade function audit: PASS
- Main-database downgrade drill: NOT EXECUTED

Normal application rollback does not use destructive database downgrade.

## Rollback Evidence Boundary

Application rollback strategy is documented as:

known-good Git commit
-> rebuild application images
-> production Compose deployment
-> dependency/service health verification
-> application smoke verification

The current production Compose configuration uses build-based application images rather than immutable commit-tagged application images.

Therefore:
- Immutable image rollback: NOT VERIFIED / NOT IMPLEMENTED
- Git/Compose rollback strategy: DOCUMENTED
- Destructive production rollback drill: NOT EXECUTED
- Production restore drill: NOT EXECUTED
- Production RPO: NOT MEASURED
- Production RTO: NOT MEASURED

These are intentional evidence boundaries, not failed local acceptance gates.

## Final Local Readiness

- Local runtime hardening: PASS
- Product acceptance: PASS
- PostgreSQL backup: PASS
- PostgreSQL restore verification: PASS
- Migration graph integrity: PASS
- Rollback strategy documentation: PASS
- Backup Git exclusion: PASS
- Working tree: expected CLEAN after final documentation commit

## External Acceptance Boundary

The following are NOT claimed:

- external production deployment
- external production certification
- Vendor acceptance
- Reseller acceptance
- Customer acceptance
- measured production RPO/RTO
- production rollback drill
- production restore drill

## Conclusion

LOCAL FINAL DELIVERY EVIDENCE: PASS

The local production-like validation and recovery evidence is complete within the documented scope.

External production deployment and downstream Vendor/Reseller/Customer acceptance remain separate future events and require independent evidence.
