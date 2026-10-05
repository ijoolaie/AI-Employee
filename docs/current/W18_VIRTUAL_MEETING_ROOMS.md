# W18 Virtual Meeting Rooms

**Status:** FOUNDATION IN PROGRESS — post-v1.4.16 mainline
**Issue:** #902
**Reconciled:** 2026-10-05

## 1. Purpose

W18 introduces a governed Meeting/Session domain for virtual meeting-room presentation and lifecycle state.

The meeting layer is downstream of Workforce Core:

Employee / WorkItem / Run / Workflow / Approval / Audit
                         ↓
                 Meeting evidence
                         ↓
                 Meeting / Room state
                         ↓
                       UI

Meeting state must never become a second source of truth for execution or authorization.

## 2. First vertical slice

A Meeting is a tenant-scoped durable session with:

- stable identity;
- title and optional description;
- bounded lifecycle: scheduled, active, paused, ended, cancelled;
- participant membership;
- participant presentation role;
- optional authoritative Employee, WorkItem and Run references;
- scheduled/start/end timestamps;
- evidence status/version.

Participant roles are presentation/session roles only. They never grant tools, permissions, approvals, quotas or billing authority.

## 3. Evidence semantics

- VERIFIED: directly linked to authoritative persisted Workforce evidence;
- UNKNOWN: no authoritative evidence establishes the requested relation;
- NOT_APPLICABLE: relation does not apply;
- UNVERIFIED: a candidate relation exists without the required evidence.

No synthetic participant activity, transcript, project progress, KPI, customer outcome or business result may be created merely for visual realism.

## 4. Tenant boundary

Every Meeting and MeetingParticipant is tenant-scoped.

Reads for another tenant fail closed. Participant Employee references must resolve within the same tenant unless the platform has an explicit governed system-employee sharing contract.

## 5. API

First read-only presentation endpoint:

GET /api/v1/customer-dashboard/meetings/{meeting_id}

The response exposes only durable meeting state and authoritative evidence references. It does not mutate meeting state or execution state.

## 6. Future boundaries

W18 does not itself introduce:

- voice/TTS;
- video/camera;
- real-time avatar generation;
- external conferencing providers;
- synthetic transcripts;
- autonomous external messaging.

Those belong to later provider contracts and W19 unless a separately governed provider slice is explicitly added.

## 7. Definition of Done

semantic contract → Meeting/Session domain → tenant-safe API → tests → real PostgreSQL evidence → CI → documentation reconciliation

All W18 work remains post-v1.4.16 engineering evidence and requires fresh exact-SHA certification before any release promotion.
