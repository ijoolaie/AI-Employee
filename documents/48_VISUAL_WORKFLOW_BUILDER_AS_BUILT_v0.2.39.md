# Visual Workflow Builder — As Built v0.2.39

## Scope
Phase 1 Visual Workflow Builder is implemented as a customer-facing version editor for the existing immutable WorkflowVersion API.

## Implemented
- Workflow builder route: `/workflows/{workflow_id}/builder`.
- Node palette for Employee, Condition, Approval and Parallel.
- Native drag/drop reordering of the linear step path.
- Node duplication and deletion.
- Properties editor for step key, employee ID, approval message, condition reference/value, retry attempts and timeout.
- Trigger selection: manual, schedule, event/webhook.
- Activation toggle when saving a new version.
- Current WorkflowVersion loading and editing.
- Version creation through the existing immutable backend API.
- Version history with current-version marker and content hash.
- Builder links from Workflow catalog and Workflow detail.

## Contract
The builder does not mutate an existing immutable version. Save creates a new `WorkflowVersion` through `POST /api/v1/workflows/{workflow_id}/versions`.

## Verification
- Source-level TypeScript/JSX structure inspected.
- Backend version API already exists and accepts the builder payload.
- Full Next.js build is not claimed unless dependencies are installed and `next build` completes.

## Known limitation
This is the Phase 1 functional builder foundation. A richer graph editor with arbitrary edge routing, nested visual branch editing, validation previews and collaborative editing can be added later without changing the immutable version contract.
