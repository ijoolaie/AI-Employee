# RC8 Modular Architecture — M2

## Implemented
M1 Employee bounded modules plus M2 bounded-context shells for:
- Workflow / Automation
- Knowledge / RAG / Memory
- CRM / Customer Experience
- Commerce / Orders / Shopify
- Billing / Usage / Entitlements

Existing legacy implementation paths remain compatible. This release
establishes boundaries before moving implementation code.

## Dependency rules
- A bounded context owns its application/domain behavior.
- API is an adapter and should call application interfaces.
- Domain code must not import API code.
- External providers must be accessed through infrastructure adapters.
- Cross-context behavior should use commands/queries/events rather than
  importing another context's service implementation.
- Shared kernel contains only stable primitives/contracts/events.
- Compatibility facades are temporary migration aids.

## Migration sequence
M1 Employee modules: completed.
M2 Bounded-context shells: completed.
M3 Move repositories and infrastructure behind module interfaces.
M4 Replace direct cross-context service calls with events/commands.
M5 Frontend domain API clients.
M6 CI architecture gates and remove legacy facades after verification.
