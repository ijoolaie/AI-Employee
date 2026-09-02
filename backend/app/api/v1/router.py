"""Aggregate API v1 routers."""

from fastapi import APIRouter

from app.api.v1 import work_items, test_center, test_center_evidence, api_keys, admin, approvals, auth, employees, feedback, files, runs, usage, knowledge, memory, workflows, workflow_events, workflow_schedules, workflow_approvals, operations, customer_dashboard, billing, billing_webhooks, invoices, orders, sales, customer_channels, public_chat, products, commerce_integrations, onboarding, inbox, customers, channel_webhooks, sales_readiness, tenant_admin, reseller_admin, admin_providers, edition_control, license_control

api_router = APIRouter()
api_router.include_router(work_items.router)
api_router.include_router(test_center.router)
api_router.include_router(test_center_evidence.router)
api_router.include_router(auth.router)
api_router.include_router(api_keys.router)
api_router.include_router(admin.router)
api_router.include_router(admin_providers.router)
api_router.include_router(edition_control.router)
api_router.include_router(license_control.router)
