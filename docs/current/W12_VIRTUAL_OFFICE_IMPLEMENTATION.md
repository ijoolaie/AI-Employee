# W12 — Virtual Office Foundation

**Date:** 2026-10-03  
**Scope:** post-v1.4.11 mainline engineering  
**Current certification:** NOT RUN / NOT VERIFIED  
**Release tag:** NONE

## Purpose

W12 introduces the first visual **AI Company Headquarters** presentation layer without creating a second operational runtime.

The Virtual Office is a read-only visualization of governed Workforce Core state.

## Implemented contract

### API

GET /api/v1/customer-dashboard/office

The endpoint is tenant-scoped through the existing authenticated AuditReadContext.

Response includes employee count, counts by presentation state, employee identity and avatar reference, latest Employee Run identifier/status/timestamp, office state and generation timestamp.

### State derivation

The implementation reads existing Employee, Run, WorkflowStepRun and WorkflowApproval records. No new operational state database/table was introduced.

Current mappings:
- active employee + pending/queued/running latest Run → WORKING;
- latest Run associated with a pending workflow approval → WAITING_APPROVAL;
- latest Run failed → ESCALATED;
- latest Run cancelled → BLOCKED;
- terminal/no Run/inactive → IDLE.

MEETING, richer project states and department-specific states are intentionally not fabricated because their underlying runtime/session contracts are not yet implemented.

## Frontend

Route: /office

Implemented:
- Executive/CEO desk presentation;
- live employee floor;
- employee cards;
- stable avatar rendering;
- live state badges;
- latest Run reference;
- navigation entry;
- dashboard shortcut;
- five-second read refresh.

The UI is presentation-only. It cannot create permissions, approvals or execution authority.

## Security / governance boundary

- Tenant isolation uses the existing authenticated customer context.
- Employee state is derived from tenant-owned records.
- Avatar URLs remain inert presentation metadata.
- No provider, camera, GPU, video or voice execution is introduced.
- No generic shell path is introduced.
- No commercial entitlement is inferred by the frontend.

## Deferred W12/W13+ scope

Not implemented:
- office tiers based on spend/projects/employees;
- department/floor/campus clustering;
- employee appearance/gender/clothing customization;
- wardrobe/cosmetic commerce;
- skills marketplace;
- career/reputation presentation;
- virtual meetings;
- voice/TTS;
- real-time avatar/video;
- third-party Employee marketplace.

## Evidence

This implementation is post-v1.4.11 mainline work.

Exact-SHA CI, product gates and production certification for the resulting mainline are NOT RUN / NOT VERIFIED at this checkpoint. Therefore no release tag or production claim is made.


## W12.2 checkpoint — current work visibility

Implemented a read-only `current_work_item` presentation field per employee when the latest governed Run is actively executing or waiting for approval. It is derived from the authoritative `Run.work_item_id` → tenant-scoped `WorkItem` relation; the office layer does not create or mutate WorkItems.

Displayed fields: WorkItem id, title, and status. No synthetic task title, progress percentage, project, department, or meeting state is generated.

Exact-SHA CI/certification remains **NOT RUN / NOT VERIFIED** after this implementation slice; no release or production deployment is claimed.


## W12.3 checkpoint — governed executive approval desk

The CEO desk now reads up to eight real pending `WorkflowApproval` records for the authenticated tenant, joined to the governed employee Run when available. The presentation includes approval id, workflow/step identity, employee identity, status, creation time, and expiry. Each item links to the existing approvals workspace; the Office layer does not approve, reject, mutate, or synthesize approval records.

Exact-SHA CI/certification remains **NOT RUN / NOT VERIFIED** after this slice. No release or production deployment is claimed.
