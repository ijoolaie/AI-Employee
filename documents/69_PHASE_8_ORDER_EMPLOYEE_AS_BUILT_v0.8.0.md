# Phase 8 As-Built — Order Employee (v0.8.0)

## Delivered
- Model `BusinessOrder` + migration `b1c2d3e4f5a8`
- `order_service` (create, status, list, summary, analyze file, link invoice)
- Tools: create_order, update_order_status, analyze_order_file, order_summary, link_order_invoice
- REST `/api/v1/orders`
- Seed `scripts/seed_order_employee.py`
- Tests `tests/test_order_service.py`
- Reuses `normalize_tax_rate` from Phase 7

## Status lifecycle
draft → confirmed → processing → shipped → delivered (or cancelled)
