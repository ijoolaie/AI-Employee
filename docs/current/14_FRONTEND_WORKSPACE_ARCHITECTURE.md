# Frontend Workspace Architecture

## Decision

The frontend is organized around three user experiences instead of one universal sidebar:

1. **Platform Control Plane** — vendor-owned administration for platform operators and human support/engineering staff.
2. **Reseller Workspace** — commercial and service operations for a reseller and its directly managed client tenants.
3. **Client Business Workspace** — day-to-day business operations for an end customer, including human employees, AI employees, customers, products, orders, workflows, and channels.

This is a workspace boundary, not merely a visual role switch.

## Routing

- `/admin/*` → Platform Control Plane
- `/reseller/*` → Reseller Workspace
- existing customer routes such as `/dashboard`, `/customers`, `/orders`, `/products`, `/employees`, `/workflows`, `/settings/*` → Client Business Workspace

Authentication now routes users according to `is_platform_admin` and `tenant_kind`.

## Platform Control Plane

The platform operator needs system-wide visibility and troubleshooting tools rather than business CRUD. The current shell intentionally focuses on:

- tenants
- operations
- audit logs
- validation
- AI providers
- internal AI employees

The internal AI workforce is a first-class platform concern. Planned internal roles include operations, HR, sales/marketing, finance, support, and executive/analytics assistants. These employees must remain in the vendor-controlled tenant and never become visible to unrelated customer tenants.

## Reseller Workspace

A reseller manages its own service organization and directly managed client portfolio. The initial implementation provides:

- client portfolio and child-tenant status controls
- reseller human service team
- reseller-owned internal AI employees
- support/workflow/usage/integration surfaces
- commercial reporting and billing surfaces
- reseller settings and security

Client data is intentionally not represented as reseller-global data. Client tenants remain the authority for their business records and client AI employees.

## Client Business Workspace

The client navigation is now business-first. It includes customers, orders, products, sales, analytics, reports, human employees, AI employees, AI workspace, customer conversations, inbox, channels, knowledge, memory, workflows, approvals, schedules, files, usage, integrations, and security/settings.

## Security model

Workspace routing is enforced in the frontend layouts for user experience and accidental navigation prevention. Backend authorization remains authoritative. A reseller endpoint is tenant-parent scoped and only returns direct child customer tenants.

`tenant_kind` is exposed by `/auth/me` so the frontend does not infer commercial authority from a URL or a client-controlled setting.

## UX principles

- Do not show platform engineering controls to resellers or clients.
- Do not show reseller portfolio controls to clients.
- Do not mix client business operations with system troubleshooting.
- Keep Security/Password under the workspace's Settings area.
- Treat AI employees as workforce resources alongside human employees, not as a developer-only feature.
- Prefer operational summaries and next actions on dashboards over technical telemetry.
- Preserve tenant boundaries in every cross-tenant support action and require explicit audited access when platform support needs to inspect a client.
