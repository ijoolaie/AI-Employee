# W13 — Customer HQ Progression

**Date:** 2026-10-03  
**Scope:** post-v1.4.12 mainline engineering  
**Status:** IMPLEMENTED — certified in `v1.4.13`

## Purpose

W13 adds deterministic Customer HQ progression metadata to the W12 Virtual Office without introducing a second operational state store or an authorization path.

## Authoritative inputs

The Office endpoint now reads tenant-scoped billing/subscription state through the existing billing service:

- subscription plan code/name/status;
- active employee count and plan employee limit;
- active workflow count and plan workflow limit;
- monthly run count and plan run limit;
- monthly token usage and plan token limit;
- truthy plan feature keys as enabled presentation capabilities.

No project, department, room, floor, performance, revenue or customer-entitlement state is fabricated when no authoritative source exists.

## HQ tier contract

The presentation tier is derived from the authoritative subscription entitlement:

- `STARTER` → starter plan;
- `BUSINESS` → business plan;
- `PROFESSIONAL` → professional plan;
- `ENTERPRISE` → enterprise plan or explicit enterprise feature;
- `CUSTOM` → unknown plan, fail-closed presentation fallback.

The tier is presentation metadata only. It does not change permissions, quotas, approvals, tenant isolation or execution authority.

## API

`GET /api/v1/customer-dashboard/office` now returns:

- `hq_tier`;
- `hq_metrics` with tenant-scoped plan, subscription, employee, workflow, run, token and enabled-capability data;
- existing W12 employee state, current work and pending approval data.

## Frontend

The `/office` view now presents:

- HQ tier;
- plan/subscription state;
- employee/workflow capacity;
- monthly run/token consumption against authoritative limits;
- an explicit presentation-only boundary.

The frontend does not calculate business entitlements or infer authorization from the tier.

## Tests

Added coverage for:

- entitlement-to-tier mapping;
- tenant-scoped authoritative metrics surfaced by the office service;
- preservation of existing W12 office state and approval behavior.

## Evidence boundary

W13 commits are after immutable release `v1.4.12` and therefore do **not** inherit its certification.

W13 exact-SHA CI/product gates and Production Certification are **VERIFIED PASS**. The implementation was included in certified release `v1.4.13` at SHA `5d57d9929cc5e924c5b9147dc0b0a41d25f39d83`.
