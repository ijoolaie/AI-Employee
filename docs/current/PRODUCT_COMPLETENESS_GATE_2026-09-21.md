# Product Completeness Gate — 2026-09-21

## Purpose

The v1.4.9 release is repository-certified, but certification validates the defined engineering/release test scope; it does not prove that every customer-facing product surface is complete.

A product-completeness review was triggered by three concrete findings:

1. Persian/RTL support exists only as a minimal i18n shell and is not a complete usable Persian product experience.
2. Employee Templates exist, but the catalog is limited to three templates and the template flow is install-only; it does not yet constitute a sufficiently complete employee starter catalog for the intended business product.
3. Several list/table surfaces and resource lifecycle actions need a systematic CRUD/lifecycle parity review; hard deletion must not be added indiscriminately where archive/deactivate/retention is safer.

## Decision

**These items are genuine product requirements and must be completed before external commercial production launch.**

They are not reasons to mutate or invalidate the immutable v1.4.9 certification. They define the next source-change work and therefore require a new candidate release and fresh certification after implementation.

## Logical assessment

| Area | Decision | Priority | Reason |
|---|---|---:|---|
| Persian + RTL | Must build to completion | P0 | Persian is explicitly the primary market language in the i18n design. Current code has only a small fa/en message catalog and a client-side direction switch; major pages still contain hard-coded English strings. |
| Employee Templates | Must expand and complete | P1 | Templates are a core onboarding/productization mechanism. The current backend catalog contains only sales_assistant, support_agent, and order_assistant; the UI only lists and installs them. A small curated catalog is preferable to an unlimited template marketplace, but the initial commercial catalog needs broader role coverage and complete template metadata/installation behavior. |
| Lists/Tables | Must complete where they represent operational resources | P0/P1 by resource | A SaaS operating platform needs usable list/detail flows, filtering/search where scale requires it, pagination where data can grow, and consistent loading/empty/error/retry states. A table is not required for every resource; cards are valid for small collections. |
| CRUD / lifecycle | Must complete by resource semantics | P0/P1 by resource | Create/edit/read are required where users own/configure a resource. Delete is not universally required: use archive/deactivate/cancel/revoke when records must remain auditable or retained. Every destructive action needs authorization, confirmation, idempotency and audit behavior. |
| Backend/frontend parity | Must verify | P0 | Existing APIs must have an intentional UI path or be explicitly internal/admin-only. UI must not advertise unsupported operations. |

## Evidence from current repository

### Persian / localization

Current frontend i18n supports only en and fa, and the provider sets document.documentElement.lang and dir after the client mounts.

The message catalog currently contains only a small set of common/navigation strings. Major customer pages still render English literals directly, including Employees, employee details, run forms, guardrails, channel publishing and run history.

Therefore the existing implementation is i18n infrastructure, not completed Persian localization.

The design document documents/22_I18n_Localization_v1.0.md already defines Persian as the primary market language and requires the Customer Panel, Admin Panel and public pages to support fa and en, with full RTL behavior.

### Employee Templates

The backend currently defines three templates:

- sales_assistant
- support_agent
- order_assistant

The public template API exposes list/install operations, and the customer template page renders cards with an install action.

This is a valid foundation, but not a complete commercial employee catalog. The next implementation should define a curated minimum catalog, not an arbitrary large number of templates.

Each production-ready template should have, at minimum:

- stable code and display name
- Persian and English name/description
- purpose and intended workflow
- input/output contract
- allowed tools
- guardrails/risk rules
- required knowledge/data dependencies
- example use case
- install action
- post-install customization path
- version/compatibility metadata
- tenant-safe installation behavior

### Lists, tables and CRUD/lifecycle

The Employees page currently provides listing and creation navigation, while the employee detail page provides execution, guardrails update and customer-channel publishing. The visible employee surface does not expose a complete resource lifecycle such as edit/archive/deactivate where applicable.

The correct product rule is not “add Delete everywhere.”

Use this lifecycle policy:

- Run/job: view, cancel/stop while active; no hard delete by default.
- Workflow/schedule: create, view, edit, enable/disable, cancel where applicable; archive/version rather than destructive delete where history matters.
- AI Employee: create, view, edit/configure, activate/deactivate, archive; hard delete only if retention/audit policy explicitly permits it.
- Files/knowledge: upload, list, inspect, download where applicable, delete/archive according to retention policy.
- Customers: create/edit/view, deactivate/anonymize/delete only through the documented privacy lifecycle.
- Users/memberships: invite, view, role/permission update, suspend/remove according to membership policy.
- Integrations/channels: create/configure, enable/disable, rotate/revoke credentials or public keys where supported; do not expose fake client-side credential CRUD.
- Approvals: view, approve/reject/cancel/expire according to state.
- Tenants: provision, view, suspend/reactivate/archive; hard deletion is exceptional.

For each operational list, the UI should provide only actions supported by the backend and authorization model.

## Required product-completeness gate

Before external production deployment of a source-changed release:

1. Complete Persian/English localization for all customer-facing core surfaces.
2. Verify true RTL behavior for shell, navigation, forms, tables/cards, dialogs, pagination, status badges and directional controls.
3. Add locale-aware date/number/currency formatting and preserve readable mixed Persian/Latin technical identifiers.
4. Define and implement the curated minimum Employee Template catalog.
5. Complete template installation/customization metadata and permissions.
6. Inventory every operational list/detail surface.
7. Map every resource to create/read/update/lifecycle actions.
8. Resolve backend/frontend parity gaps.
9. Standardize loading/empty/error/retry/success/permission-denied states.
10. Add destructive-action confirmation and audit behavior.
11. Add frontend and backend regression coverage for completed product flows.
12. Run a browser-level product acceptance pass in both fa and en.
13. Only then cut a new release candidate and rerun the required certification gates.

## Release boundary

This audit does not alter:

- v1.4.9
- certified SHA f1ce20c010779f5273eb5d0051da24cdd57b33f6
- existing certification evidence

Any implementation changes belong to a new post-v1.4.9 candidate release.

## Definition of done

The product is considered complete for this gate when:

- a Persian-speaking customer can use the core customer workflow without encountering essential untranslated UI;
- switching fa/en is persistent and deterministic;
- RTL layout is usable, not merely mirrored;
- the core employee template catalog covers the intended first commercial use cases;
- operational resources have coherent list/detail/lifecycle flows;
- destructive actions follow retention and audit rules;
- frontend actions match actual backend capabilities and authorization;
- browser-level acceptance passes in both locales;
- documentation, release identity and evidence are reconciled before commercial go-live.