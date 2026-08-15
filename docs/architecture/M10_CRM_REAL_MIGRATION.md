# M10 — CRM Real Migration

## Migrated
- Customer domain model
- Conversation domain model
- Customer repository port
- Conversation repository port
- Customer identity resolver port
- CRM application service
- Customer creation / resolution
- Conversation opening
- `crm.customer.created` event
- Legacy identity adapter
- Unit tests

## Compatibility
Existing CRM/customer lookup behavior is preserved behind an adapter. No breaking
API rewrite or database schema migration is introduced in this step.

## Next
M11 should migrate Commerce / Orders, then M12 Billing.
