# AI Employee Platform — Frontend

**v0.1.0** — Customer Panel MVP aligned with backend `v0.2.0` and docs package `v1.2` / `08_Frontend_v1.1`.

## Stack

| Technology | Role |
|---|---|
| Next.js 15 (App Router) | Framework, routing, layouts |
| React 19 + TypeScript | UI |
| Tailwind CSS | Styling |
| Zustand | Auth / session state (persisted) |
| TanStack Query | Server state (employees, runs, files) |
| React Hook Form + Zod | Forms & validation |
| Axios | API client with JWT + refresh interceptors |
| Lucide React | Icons |

## What's included (MVP)

### Auth
- Register (tenant + user)
- Login (tenant_slug + email + password)
- JWT access/refresh with automatic refresh on 401
- Protected customer routes

### Customer Panel
- **Dashboard** — employee count, run stats, cost, recent runs
- **Employees** — list, create custom employee, detail + start run
- **Runs** — list + detail with live polling while pending/queued/running
- **Files** — upload, list, soft-delete
- **Settings** — profile & tenant info

### Not yet (per roadmap)
- Admin Panel
- Developer Console (Trace / Logs)
- Knowledge, Billing, Usage charts
- Report Employee visualizations (Recharts)
- Workflow UI

## Project structure

```
frontend/
├── app/
│   ├── (auth)/          # login, register
│   ├── (customer)/      # dashboard, employees, runs, files, settings
│   ├── layout.tsx
│   ├── page.tsx         # redirect
│   └── globals.css
├── components/
│   ├── ui/              # Button, Input, Card, Badge, Spinner, EmptyState
│   ├── layout/          # Sidebar, Header
│   └── providers.tsx
├── lib/
│   ├── api.ts           # Axios client + domain functions
│   ├── auth-store.ts    # Zustand persist
│   └── utils.ts
├── types/               # Aligned with backend Pydantic schemas
└── ...
```

## Quick start

```bash
# From repo root / frontend folder
cp .env.example .env.local
# Edit NEXT_PUBLIC_API_URL if backend is not on http://localhost:8000

npm install
npm run dev
# → http://localhost:3000
```

Backend must be running (`uvicorn` + Postgres + Redis). CORS is already set for `http://localhost:3000` in backend settings.

### Dev proxy

`next.config.ts` rewrites `/api/proxy/*` → `{NEXT_PUBLIC_API_URL}/api/v1/*`.  
If `NEXT_PUBLIC_API_URL` is unset, the client uses `/api/proxy` automatically.

## Environment

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | (proxy) | Backend origin, e.g. `http://localhost:8000` |

## API mapping

| UI | Backend |
|---|---|
| Register / Login / Me | `POST /auth/register`, `/auth/login`, `GET /auth/me` |
| Employees | `GET/POST /employees`, `GET /employees/{id}` |
| Runs | `GET/POST /runs`, `GET /runs/{id}` |
| Files | `GET/POST /files`, `DELETE /files/{id}` |

All responses use the `APIResponse[T]` envelope (`success` + `data`).

## Version history

- **0.1.0** — Initial Customer Panel MVP (Auth + Dashboard + Employees + Runs + Files + Settings)


## Localization (planned — Phase 2)

Per construction doc `22_I18n_Localization_v1.0`, the product is **bilingual**:

- **Persian (`fa`)** — primary market, RTL required
- **English (`en`)** — second language

Full `next-intl` (or equivalent), message catalogs, and language switcher are **Phase 2**. MVP UI may remain English-first until then; the requirement is locked in the docs package v1.4+.

## Auth harden (v0.1.1)

- Richer API error parsing (envelope + FastAPI `detail`)
- On refresh failure → logout and redirect to `/login?reason=session`

## Current as-built note

The Run detail page now includes an execution trace assembled by the backend from durable Audit Log and AI Provider Call records. The frontend uses the backend terminal Run status `success` (not `succeeded`).

## v0.2.18 As-Built addition

- Added a tenant-scoped Usage page at `/usage`.
- The page consumes `GET /api/v1/usage/summary` and reports AI call count, tokens, recorded cost, average latency and provider/model breakdown.
- Usage is reporting-only in this release. Quotas, invoicing and billing enforcement remain separate planned capabilities.

## Sales-readiness UX
The customer workspace now includes `/onboarding`, `/products`, `/integrations`, and `/inbox`. These are the product foundations for onboarding a business, supplying live product context to AI Employees, connecting commerce systems, and handing customer conversations between AI and humans.

## RC3 customer operations

The tenant frontend now includes Customers (CRM), WhatsApp as a customer channel option, and a full Unified Inbox transcript with human takeover and human replies. New customer-facing capabilities must be represented in navigation, the relevant dashboard/workspace, onboarding and documentation before release acceptance.
