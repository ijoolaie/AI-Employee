# M7 Migration Matrix

| Context | Domain | Application | Ports | Infrastructure | Legacy Facade |
|---|---|---|---|---|---|
| Workflow | Ready | Ready | Ready | Boundary | Retained |
| Knowledge | Ready | Ready | Ready | Boundary | Retained |
| CRM | Ready | Ready | Ready | Boundary | Retained |
| Commerce | Ready | Ready | Ready | Boundary | Retained |
| Billing | Ready | Ready | Ready | Boundary | Retained |
| Employees | Existing M1 | Existing M1 | Ready | Boundary | Retained |

`Ready` means the package boundary exists and is testable; it does not claim
that every historical service implementation has already been physically moved.

## M8 update
Workflow execution use-case: **REAL APPLICATION MIGRATION COMPLETED**. Legacy engine retained only behind adapter.

## M9 update
Knowledge/RAG ingestion: **REAL APPLICATION MIGRATION COMPLETED**. Legacy parser/vector implementations retained only behind adapters.

## M10 update
CRM customer identity/conversation use-cases: **REAL APPLICATION MIGRATION COMPLETED**. Legacy CRM lookup retained only behind adapter.
