# Phase 12 — Test Center & Evidence Platform — Implementation Slice

Date: 2026-09-02

## Objective

Turn the existing acceptance and evidence contracts into a first-class,
repeatable Test Center without destabilizing the certified execution substrate.

## Scope

### P12.1 — Test Definition Contract
- Test definition identity
- Test type/category
- required tenant/workspace context
- prerequisites
- expected result
- evidence requirements

### P12.2 — Safe Test Execution
- isolated execution context
- tenant-bound execution
- authorization enforcement
- safe handling of test fixtures
- explicit prevention of cross-tenant execution

### P12.3 — Test Run Lifecycle
- queued
- running
- passed
- failed
- cancelled
- expired

Each run must retain timestamps, actor/executor identity and correlation IDs.

### P12.4 — Evidence & Artifacts
- structured pass/fail result
- logs
- artifact references
- runtime/version identity
- migration identity
- relevant SHA/checksum
- explicit evidence boundary

### P12.5 — Run History
- tenant/workspace scoped history
- role-aware visibility
- filtering by test/status/date
- immutable result history

### P12.6 — Exportable Verification Record

Produce an evidence record suitable for local delivery and future external
acceptance workflows without claiming external acceptance.


## Edition-aware test catalog

The Test Center is a shared execution/evidence platform, but its **test catalog is not required to cover every application service for every edition**.

Each definition should declare:

- `edition`: `vendor`, `reseller`, `customer`, or `shared`;
- `workspace_key`;
- `service_group`;
- `scope_type`: same-tenant, direct-child, or platform-control-plane;
- prerequisites and expected result;
- evidence requirements;
- authorization/risk level.

### Coverage contract

**Vendor**
- Test platform/control-plane services: reseller provisioning, hierarchy, entitlements, global template governance, platform audit/security, operations and approved support paths.
- Do not require routine tests for customer CRM/orders/products or every customer-only service.

**Reseller**
- Test reseller operations and directly managed customer operations: customer provisioning, portfolio, delegated entitlements, reseller workforce/workflows, usage/health, support, audit/security and enabled commercial flows.
- Do not require vendor control-plane tests or unrelated customer/reseller services.

**Customer**
- Test customer-owned business workflows: CRM/customers, products, orders/sales, human/AI employees, conversations/channels, knowledge/memory, workflows/approvals/schedules, files, analytics/reports and enabled integrations/security.
- Do not require reseller portfolio, vendor control-plane or platform-wide configuration tests.

### Shared foundation tests

Authentication/session context, tenant isolation/RBAC, audit, approval/policy enforcement, safe execution and evidence integrity are shared foundations. They should be tested at the shared boundary and then supplemented by focused edition-specific positive/negative tests, rather than duplicated across every service.

### Required boundary negatives

The catalog must contain targeted negative tests for:

- Vendor → Customer ordinary business access denied unless an explicit audited support path exists.
- Reseller → Vendor and sibling/unrelated tenant access denied.
- Customer → parent Reseller control plane and sibling/unrelated tenant access denied.

These tests prove the edition boundary without forcing every edition to execute the full application service catalog.

## Non-Goals

- No replacement of the existing certified acceptance suite.
- No new external production dependency.
- No fake monitoring/alert-provider integration.
- No destructive database migration or rollback.
- No weakening of existing tenant/RBAC/audit controls.
- No modification of the canonical v1.3.2 release identity.

## Definition of Done

- Test definitions have stable identifiers and tenant/workspace boundaries.
- Test execution is authorization-aware and safely isolated.
- Test runs have durable lifecycle state and correlation.
- Results and artifacts are queryable and tenant-scoped.
- Evidence records preserve runtime/release/migration identity.
- Existing Product Acceptance evidence remains valid without rerunning it.
- Backend tests cover positive and negative authorization/tenant paths.
- Frontend exposes the Test Center only through authorized workspace boundaries.
- No regression is introduced into the unified Human/Agent execution model.

## First Engineering Slice

Implement P12.1 + P12.2 + the minimum P12.3 persistence/API contract first.

Do not begin with the full UI.

The first vertical slice should be:

**Test Definition → authorized Test Run creation → isolated execution context → Run lifecycle → persisted result → tenant-scoped retrieval → audit/evidence record.**

After this slice passes backend contract tests, add the Test Center UI and
export functionality incrementally.

## Acceptance Boundary

Phase 12 implementation evidence is engineering/product evidence.

It does not constitute external production certification, Vendor acceptance,
Reseller acceptance or Customer acceptance.
