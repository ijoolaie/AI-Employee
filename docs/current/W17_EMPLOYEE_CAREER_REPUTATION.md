# W17 Employee Career & Reputation

**Status:** IMPLEMENTED / REAL-STACK VERIFIED — post-v1.4.16 mainline
**Reconciled:** 2026-10-05
**Issue:** #897

## 1. Purpose

W17 adds a governed presentation/read model for an Employee's career history and reputation. It must consume authoritative Workforce evidence and must never create operational authority.

The design principle is:

Employee / WorkItem / Run / Workflow / Approval / Audit / Business metrics
                              ↓
                    W17 evidence mapping
                              ↓
                 Career / Reputation read model
                              ↓
                         UI / API

No W17 state may become a second source of truth for execution.

## 2. Scope for the first vertical slice

### Career

- Identity: Employee stable identity (Employee.id, name, slug).
- Tenure: derived from authoritative Employee lifecycle timestamps. The initial implementation must not invent a start date; if historical employment start is unavailable, tenure is UNKNOWN.
- Work history: derived from tenant-scoped WorkItems and Runs associated with the Employee where the relationship is authoritative.
- Completed work: count only terminal successful records that satisfy the selected evidence contract. Cancelled/failed/blocked work is not successful completion.
- Projects: only expose project-level history where an authoritative project/workflow relation exists. Do not infer projects from titles or LLM text.

### Reputation

The first slice should prefer evidence cards and verified indicators over a single score. If a score is later introduced, it must be deterministic, versioned, explainable and reproducible from stored evidence.

Candidate verified indicators:
- successful governed runs;
- successful WorkItems;
- approval-compliant delivery;
- verified operational KPI observations;
- incident/recovery outcomes where authoritative evidence exists.

Unverified indicators must be explicitly marked UNKNOWN / UNVERIFIED, never converted to zero.

### Achievements / badges

Badges are presentation metadata, not authority. Every badge must have:
- stable badge code;
- human-readable label;
- evidence type;
- evidence reference(s);
- achieved-at timestamp from authoritative evidence;
- tenant scope;
- immutable or versioned definition.

A model may suggest a badge, but it cannot make the badge authoritative without the required evidence and governance path.

## 3. Tenant and authorization boundary

All W17 reads are tenant-scoped. System employees must not leak cross-tenant operational history.

A request for an employee outside the caller tenant must fail closed according to the existing API not-found/authorization contract.

W17 fields cannot modify:
- allowed tools;
- role bindings;
- approvals;
- quotas;
- billing;
- execution state;
- provider selection.

## 4. Evidence semantics

| State | Meaning |
|---|---|
| VERIFIED | Directly derived from authoritative persisted evidence |
| UNVERIFIED | A candidate signal exists but the required authoritative evidence is missing |
| UNKNOWN | The platform cannot establish the fact from available records |
| NOT_APPLICABLE | The metric does not apply to this employee/scope |

The implementation must preserve evidence provenance at the field/indicator level where practical.

## 5. API direction

Initial API should be read-only and tenant-scoped, for example:

GET /api/v1/customer-dashboard/employees/{employee_id}/career

The response should contain:
- employee identity/presentation-safe fields;
- tenure state;
- verified work-history summary;
- verified KPI/indicator cards;
- achievement/badge cards with evidence references;
- explicit evidence status;
- contract version.

The exact route/schema is subject to repository conventions discovered during implementation; this document is the semantic contract, not permission to bypass existing API patterns.

## 6. Persistence rule

Do not add a new mutable career/reputation table unless the implementation proves that an authoritative durable source cannot provide the required state.

Derived career history should be computed from existing durable records where possible. If badges or manually curated career metadata require persistence, use a tenant-scoped, auditable domain with explicit provenance and no execution authority.

## 7. Test requirements

Minimum tests:
1. same-tenant employee career read succeeds;
2. cross-tenant employee read fails closed;
3. tenure is UNKNOWN when authoritative start evidence is absent;
4. successful WorkItems/Runs are counted only from authoritative terminal states;
5. failed/cancelled/blocked work is not counted as completed;
6. missing KPI evidence is UNKNOWN/UNVERIFIED, not zero;
7. badge without required evidence is rejected or remains non-authoritative;
8. W17 output cannot change employee permissions/tools/approvals/billing;
9. response contract includes evidence status/version;
10. real PostgreSQL test covers the complete read path and tenant boundary.

## 8. Real-stack evidence

W17 real-stack verification passed on the dedicated PR verification head `f8b5a9734acbcc70ad165a2fbda2f326bfc2fa9a`.

- Workflow: `Workforce W17 Career Reputation E2E`
- Run: `37298325542` — PASS
- Job: `111724800314` — PASS
- CodeQL on the same verification head: Run `37298325646` — PASS
- Verified path: real PostgreSQL stack → migration/head validation → application health → source compilation → W17 career API E2E → tenant isolation → clean shutdown.
- The E2E verified successful Run/WorkItem counts, failed-record exclusion, UNKNOWN tenure, NOT_APPLICABLE reputation score and cross-tenant 404.

The verification head differed from the subsequent main merge only by a workflow comment; no W17 application behavior changed. This is engineering evidence, not Production Certification.

Any provider or external commercial evidence must remain separate from W17 career/reputation evidence.

## 9. Release boundary

All W17 work is post-v1.4.16 mainline engineering until a new exact-SHA Production Certification is run. No W17 commit inherits certification from v1.4.16.
