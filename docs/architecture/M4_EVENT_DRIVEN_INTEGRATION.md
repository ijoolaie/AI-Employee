# M4 — Event-Driven Module Integration

## Implemented
- DomainEvent, ModuleCommand and ModuleQuery contracts.
- Stable event catalog.
- Deterministic in-process event bus for local composition/tests.
- Central event wiring.
- Module-local event handlers.
- Architecture tests blocking direct imports between bounded contexts.

## Rule
Bounded contexts must not import another context's implementation.
Use commands/queries for synchronous intent/read operations and domain events
for asynchronous side effects.

## Safety
The existing durable queue/outbox implementation is not replaced in M4.
The local bus is a contract-level implementation. Real production events can
be wired to the existing durable infrastructure in the next migration.

## Example flows
commerce.order.completed -> billing/workflow
billing.payment.succeeded -> workflow
crm.customer.created -> workflow
knowledge.document.ingested -> workflow
