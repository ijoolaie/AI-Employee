# M2 Migration Plan

1. Workflow: move orchestration/application services into `modules/workflow`.
2. Knowledge: move RAG/memory orchestration into `modules/knowledge`.
3. CRM: move customer/conversation/inbox application services into `modules/crm`.
4. Commerce: move order/product/Shopify orchestration into `modules/commerce`.
5. Billing: move billing/usage/entitlement orchestration into `modules/billing`.
6. Introduce repository interfaces per module before moving persistence code.
7. Replace direct module-to-module imports with shared commands/events.
8. Only then remove legacy service facades.

No database migration is required for this structural step.
