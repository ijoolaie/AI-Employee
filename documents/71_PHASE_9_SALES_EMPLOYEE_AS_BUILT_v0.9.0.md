# Phase 9 As-Built — Sales Employee (v0.9.0)

## Delivered
- Model `BusinessDeal` + migration `c2d3e4f5a6b9`
- `sales_service`: create, stage update, list, pipeline summary, simple forecast
- Tools: create_deal, update_deal_stage, sales_pipeline_summary, sales_forecast
- REST under `/api/v1/sales`
- Seed `scripts/seed_sales_employee.py`
- Tests `tests/test_sales_service.py`

## Stages
lead → qualified → proposal → negotiation → won | lost

## Forecast
`weighted_open_deals_by_close_date` — auditable, not ML.

## Verification

The Phase 9 frontend contract surface is included in the current frontend contract suite, which was executed on 2026-08-11 with:

**105 passed, 0 failed**

The package contains two Sales Employee service test functions covering:
- allowed sales stages;
- default stage probabilities.

A fresh complete backend pytest run was not claimed during the current handoff audit because the review environment lacked `asyncpg`.

The current migration head is `0a1b2c3d4e5f`; `c2d3e4f5a6b9` is the Business Deals migration and is not the final head.
