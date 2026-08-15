# M14 — Legacy Cleanup

All migrated contexts retain compatibility adapters intentionally. Destructive deletion is blocked until caller inventory and tests are green.

## Legacy inventory at M14
- `backend/app/services/workflow_service.py`
- `backend/app/modules/commerce/infrastructure/adapters.py`
- `backend/app/modules/billing/infrastructure/adapters.py`
- `backend/app/modules/workflow/infrastructure/legacy_executor.py`
- `backend/app/modules/employees/infrastructure/adapters.py`
- `backend/app/modules/crm/infrastructure/legacy_identity.py`
- `backend/app/modules/knowledge/infrastructure/legacy_embedding.py`
- `backend/app/modules/knowledge/infrastructure/legacy_parser.py`

Cleanup policy: migrate callers -> run tests -> mark deprecated -> remove in a dedicated release.
