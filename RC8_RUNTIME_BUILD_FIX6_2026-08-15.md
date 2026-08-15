# RC8 Runtime Build Fix 6 — 2026-08-15

Fixed the frontend React Query contract mismatch in `frontend/app/(customer)/invoices/page.tsx`:
`queryFn:listInvoices` → `queryFn:()=>listInvoices()`.

This prevents TanStack Query from passing `QueryFunctionContext` into the API function's optional `status` parameter.

Previous runtime fixes are preserved in this candidate.
