# SaaS Database Design v1.3.1

## New Core Tables

### tenants
- id
- name
- status
- plan_id
- created_at

### subscriptions
- id
- tenant_id
- plan
- status
- renewal_date

### plans
- id
- name
- limits
- features

### usage_events
- id
- tenant_id
- event_type
- quantity
- timestamp

### invoices
- id
- tenant_id
- amount
- status

## Rules

All tables containing customer data must support tenant isolation.

## Migration Strategy

Incremental Alembic migrations only.
