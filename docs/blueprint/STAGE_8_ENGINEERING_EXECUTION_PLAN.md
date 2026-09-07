# Stage 8 — AI Company Operating Model Engineering Execution Plan

## Status

**Architecture / Engineering Plan — planned**

Release baseline remains **v1.3.8**. Architecture baseline is **V1.5**. This document defines the engineering work required to turn the Stage 8 workforce blueprint into an implemented, testable capability. It does not claim implementation merely because the design exists.

## 1. Objective

Implement a governed AI workforce platform in which a role can move from reusable definition to evaluated template to tenant-scoped active AgentInstance, while preserving identity, permissions, approvals, auditability, usage/cost attribution and lifecycle control.

The target model is:

```text
AgentDefinition
      ↓
AgentTemplate
      ↓
Evaluation Gate
      ↓
Approval / Publication
      ↓
AgentInstance
      ↓
Identity + RBAC + Tool Policy
      ↓
WorkItem / Workflow execution
      ↓
Audit + Usage + Cost + Health
      ↓
Review / Suspend / Replace / Retire
```

## 2. Engineering principles

1. **Agent is a first-class principal.** Every active AgentInstance has a unique identity and accountable owner/sponsor.
2. **Least privilege is enforced, not documented.** Tool, data and action scopes are explicit and checked at execution time.
3. **Authorization is per action.** Session-level authorization alone is insufficient.
4. **High-impact actions require policy gates.** Financial, legal, security-sensitive, destructive, external-send and production-impacting actions require approval according to risk policy.
5. **Tenant isolation is mandatory.** Definitions may be platform-global, but instances, credentials, memory, execution history, usage and data remain tenant-scoped.
6. **Agent-to-agent calls are trust decisions.** Caller identity, target identity, delegated authority and permitted capability must be checked.
7. **Every execution is attributable.** Audit records must identify tenant, agent, WorkItem, workflow, tool, action, target, authorization decision and correlation ID.
8. **Lifecycle is executable.** Create, activate, suspend, resume, replace and retire are state transitions, not informal flags.
9. **Cost is a control.** Agent, workflow and tenant budgets must be enforced before runaway execution becomes an incident.
10. **Documentation is not evidence of implementation.** Completion requires code, tests and release evidence on the relevant SHA.

These controls align with current enterprise agent-security guidance emphasizing unique agent identity, named ownership, least-privilege scopes, explicit tool authorization, lifecycle governance, auditability and revocation. citeturn0search0turn0search1turn0search5

## 3. Domain model

### 3.1 AgentDefinition

Canonical capability/role definition.

Required fields:

- id
- slug
- name
- description
- purpose
- responsibilities
- capability_contract
- risk_tier
- default_autonomy
- allowed_tools
- knowledge_policy
- memory_policy
- approval_policy
- evaluation_suite_id
- owner_role
- status
- version

### 3.2 AgentTemplate

Installable product packaging of an AgentDefinition.

Required fields:

- id
- agent_definition_id
- version
- publisher
- package_metadata
- compatibility
- declared_tools
- declared_permissions
- risk_metadata
- evaluation_status
- publication_status
- changelog

### 3.3 AgentInstance

Tenant-scoped active employee.

Required fields:

- id
- tenant_id
- agent_definition_id
- template_id
- template_version
- display_name
- identity_id
- sponsor_id
- operational_owner_id
- permission_set_id
- credential_refs
- memory_namespace
- lifecycle_state
- risk_tier
- autonomy_level
- cost_budget_id
- created_at
- activated_at
- suspended_at
- retired_at

### 3.4 WorkItem

The common execution unit used regardless of whether work is performed by a human or agent.

Required fields:

- id
- tenant_id
- capability_type
- input_contract
- output_contract
- priority
- risk_classification
- assigned_executor
- execution_mode
- approval_policy
- tool_policy
- deadline / SLA
- parent_workflow_id
- execution_history
- audit_metadata

### 3.5 Supporting entities

Engineering must also model, where not already present:

- AgentIdentity
- AgentSponsor
- AgentPermissionSet
- AgentToolBinding
- AgentApprovalPolicy
- AgentEvaluation
- AgentLifecycleEvent
- AgentAuditEvent
- AgentUsageRecord
- AgentBudget
- AgentHealthSnapshot
- AgentTeam
- WorkforceProposal
- BoardDecision
- ApprovalRequest
- AgentHandoff
- AgentIncident
- AgentVersionLineage

## 4. Lifecycle state machine

```text
DRAFT
  ↓
PROPOSED
  ↓
UNDER_REVIEW
  ↓
APPROVED
  ↓
EVALUATING
  ↓
PUBLISHED
  ↓
INSTALLING
  ↓
ACTIVE
  ├── SUSPENDED
  │      ↓
  │    ACTIVE
  ├── REPLACEMENT_PENDING
  │      ↓
  │    ACTIVE
  └── RETIREMENT_PENDING
         ↓
       RETIRED
```

Invalid transitions must be rejected by the domain service, not merely hidden by UI.

## 5. Identity and authorization boundary

The authorization service must answer an explicit question for every protected action:

```text
Can principal P perform action A on resource R
for tenant T in context C under policy G?
```

The answer must consider:

- authenticated principal;
- tenant;
- AgentInstance;
- sponsor/owner;
- effective RBAC/ABAC scopes;
- tool binding;
- resource ownership;
- risk tier;
- approval state;
- current WorkItem;
- delegation/handoff context;
- budget and rate limits;
- lifecycle state.

No model output may directly grant itself permissions.

## 6. Tool authorization

Every tool binding must declare:

- tool identity;
- operation/action;
- allowed resource scope;
- allowed tenant scope;
- risk tier;
- data sensitivity;
- approval requirement;
- rate/volume limit;
- timeout;
- audit requirements.

High-risk operations such as delete, export, purchase/payment, privilege change, production mutation and external send require explicit policy evaluation and, where configured, fresh human approval. Current enterprise guidance specifically recommends per-tool least privilege and authorization on every action. citeturn0search5turn0search8

## 7. Agent-to-agent authorization

Agent A calling Agent B must not be treated as an internal unrestricted call.

Required checks:

1. caller identity is valid;
2. caller lifecycle state is ACTIVE;
3. caller has delegation permission;
4. target AgentInstance is ACTIVE;
5. requested capability is exposed by target definition;
6. caller's tenant matches target tenant unless an explicitly approved cross-tenant platform operation exists;
7. delegated scope does not exceed caller's effective authority;
8. target-side policy accepts the request;
9. correlation ID is preserved;
10. resulting action is auditable.

## 8. Approval engine

ApprovalRequest must include:

- requested action;
- actor/agent;
- target resource;
- tenant;
- reason/context;
- risk classification;
- proposed tool call;
- expected impact;
- rollback/recovery information;
- expiration time;
- approver policy;
- decision;
- decision timestamp;
- evidence reference.

Approval must be bound to the exact action and target, not a vague session permission.

## 9. Workforce Manager / Internal Manager

The Internal Manager becomes the orchestration point for workforce capacity, but it cannot bypass reserved CEO authority.

Responsibilities:

- detect capability gaps;
- inspect existing templates;
- recommend staffing changes;
- create WorkforceProposal;
- prioritize workload;
- route WorkItems;
- monitor SLA and queue health;
- recommend scale-up/down;
- initiate evaluation/replacement proposals;
- initiate retirement proposals;
- escalate exceptions.

CEO-reserved actions:

- creation of critical/high-impact workforce roles;
- major strategy changes;
- high-risk organizational actions;
- irreversible actions;
- policy exceptions;
- retirement of critical governance/security agents.

## 10. AI Board integration

Board members are advisory/governance agents. They can produce structured decision packages, risk assessments and recommendations, but the CEO remains the final authority.

A BoardDecision must capture:

- proposal ID;
- board participants;
- individual recommendations;
- conflicts/uncertainty;
- risk summary;
- dissent where applicable;
- recommendation;
- CEO decision;
- final rationale;
- timestamp.

## 11. Evaluation framework

Every AgentDefinition/Template must map to an evaluation suite appropriate to its risk tier.

Minimum suites:

- functional behavior;
- authorization/RBAC;
- tenant isolation;
- tool scope enforcement;
- prompt/context injection resistance;
- memory isolation;
- handoff correctness;
- approval correctness;
- failure recovery;
- cost limits;
- observability;
- regression;
- policy compliance.

High-impact agents additionally require security, privacy, legal/compliance and adversarial evaluation as applicable.

## 12. Memory boundary

Memory must be scoped at minimum by:

```text
Platform
  └── Tenant
       └── AgentInstance
            └── WorkItem / conversation scope
```

Memory access must be authorized like any other protected resource. Persistent memory must have retention and deletion policy, and the system must defend against memory poisoning. Current enterprise guidance explicitly treats memory isolation, retention and poisoning defense as agent security concerns. citeturn0search1turn0search5

## 13. Usage, cost and budgets

Every model/tool execution must be attributable to:

- tenant;
- AgentInstance;
- WorkItem;
- workflow;
- model/provider;
- tool;
- tokens/compute where available;
- monetary estimate;
- timestamp.

Budget enforcement levels:

- per execution;
- per WorkItem;
- per AgentInstance;
- per team;
- per tenant;
- platform-wide safety limit.

Exceeding a hard budget must stop or suspend execution according to policy rather than merely generating a warning.

## 14. Audit event contract

Every meaningful agent action should emit a structured event containing:

- event_id;
- timestamp;
- tenant_id;
- actor_type;
- actor_id;
- sponsor_id;
- WorkItem_id;
- workflow_id;
- action;
- resource_type;
- resource_id;
- tool_id;
- authorization_decision;
- approval_id if applicable;
- correlation_id;
- result/status;
- cost metadata;
- policy/version metadata.

Audit events must be append-oriented and protected from ordinary agent mutation.

## 15. APIs to implement

The first engineering API surface should cover:

### Agent definitions

- `POST /agent-definitions`
- `GET /agent-definitions`
- `GET /agent-definitions/{id}`
- `PATCH /agent-definitions/{id}`
- `POST /agent-definitions/{id}/versions`

### Templates

- `POST /agent-templates`
- `GET /agent-templates`
- `GET /agent-templates/{id}`
- `POST /agent-templates/{id}/evaluate`
- `POST /agent-templates/{id}/publish`

### Instances

- `POST /agent-instances`
- `GET /agent-instances`
- `GET /agent-instances/{id}`
- `POST /agent-instances/{id}/activate`
- `POST /agent-instances/{id}/suspend`
- `POST /agent-instances/{id}/resume`
- `POST /agent-instances/{id}/replace`
- `POST /agent-instances/{id}/retire`

### Workforce

- `POST /workforce-proposals`
- `GET /workforce-proposals`
- `POST /workforce-proposals/{id}/review`
- `POST /workforce-proposals/{id}/approve`
- `POST /workforce-proposals/{id}/reject`

### Approvals

- `GET /approvals`
- `GET /approvals/{id}`
- `POST /approvals/{id}/approve`
- `POST /approvals/{id}/reject`

### Registry / health / audit

- `GET /agent-registry`
- `GET /agent-instances/{id}/health`
- `GET /agent-instances/{id}/usage`
- `GET /agent-instances/{id}/audit`

Exact routes must follow the repository's existing API conventions; these are the target contracts, not a claim that they already exist.

## 16. UI surfaces

Stage 8 UI should expose:

1. **Workforce** — active employees, managers, teams and capacity.
2. **Agent Registry** — every active/dormant instance and ownership.
3. **Role Catalog** — definitions and templates.
4. **Workforce Proposals** — staffing recommendations and decisions.
5. **Approvals** — pending high-impact actions.
6. **Agent Detail** — identity, sponsor, permissions, health, usage, incidents and lineage.
7. **Team Detail** — hierarchy, capabilities, workload and cost.
8. **Evaluation Center** — evaluation runs and evidence.
9. **Audit** — searchable execution trail.
10. **Cost/Usage** — tenant/team/agent budgets and attribution.

## 17. Implementation order

### Stage 8.1 — Domain foundation

- entities and migrations;
- lifecycle state machine;
- AgentDefinition/Template/Instance separation;
- tenant scoping;
- repository/service boundaries;
- contract tests.

### Stage 8.2 — Identity and authorization

- AgentIdentity;
- sponsor/owner;
- RBAC/ABAC enforcement;
- tool binding;
- per-action authorization;
- agent-to-agent trust;
- revocation/kill-switch.

### Stage 8.3 — Workforce orchestration

- WorkItem assignment;
- Internal Manager service;
- workforce proposals;
- board decision records;
- CEO approval boundary;
- team composition.

### Stage 8.4 — Evaluation and publication

- evaluation registry;
- risk-tier suites;
- publication gates;
- template version lineage;
- regression evidence.

### Stage 8.5 — Approvals and execution controls

- ApprovalRequest;
- approval policy engine;
- exact-action binding;
- financial/legal/security gates;
- rollback metadata.

### Stage 8.6 — Observability and economics

- audit events;
- health snapshots;
- usage metering;
- cost attribution;
- budget enforcement;
- incident integration.

### Stage 8.7 — Customer marketplace

- customer template catalog;
- safe installation;
- tenant-scoped instances;
- configuration within policy;
- customer admin lifecycle;
- installation/evaluation evidence.

### Stage 8.8 — End-to-end certification

- full workforce lifecycle E2E;
- tenant isolation E2E;
- RBAC/authorization E2E;
- approval E2E;
- agent-to-agent E2E;
- memory isolation E2E;
- budget enforcement E2E;
- audit completeness E2E;
- customer installation E2E;
- production evidence on the release SHA.

## 18. Required engineering tests

### Security

- cross-tenant access denied;
- privilege escalation denied;
- unauthorized tool denied;
- revoked agent denied;
- retired agent denied;
- agent-to-agent unauthorized call denied;
- credential material never exposed to model context;
- audit event cannot be altered by agent.

### Governance

- CEO-only actions cannot be approved by ordinary agents;
- high-risk actions cannot bypass approval;
- proposal cannot activate an agent before required gates;
- publication cannot occur after failed evaluation;
- critical agent retirement follows reserved policy.

### Operations

- queue assignment;
- handoff;
- escalation;
- retry;
- timeout;
- circuit breaker;
- kill-switch;
- recovery.

### Economics

- budget warning;
- hard budget stop;
- per-agent attribution;
- per-tenant attribution;
- cost aggregation;
- runaway-loop protection.

## 19. Exit criteria

Stage 8 engineering is complete only when the following are demonstrated on a real release candidate:

- [ ] AgentDefinition, AgentTemplate and AgentInstance are distinct enforced concepts.
- [ ] Every active agent has unique identity and human sponsor/owner.
- [ ] Tenant isolation is enforced at data, memory, tools and execution boundaries.
- [ ] Per-action authorization is enforced.
- [ ] Agent-to-agent trust is explicit and auditable.
- [ ] Risk tiers determine autonomy and approval requirements.
- [ ] High-impact actions cannot bypass approval.
- [ ] Workforce creation and retirement are governed lifecycle transitions.
- [ ] Evaluation gates block unsafe publication.
- [ ] Usage and cost are attributable and budgeted.
- [ ] Audit records are complete and searchable.
- [ ] Kill-switch/revocation is tested.
- [ ] Customer installation is tenant-safe.
- [ ] End-to-end evidence exists for the release SHA.

## 20. Evidence boundary

The architecture and engineering plan are design artifacts. They must never be cited as proof that a control is implemented.

Implementation status must be established from:

1. source code;
2. migrations/schema;
3. API and UI tests;
4. integration/E2E tests;
5. security tests;
6. CI evidence;
7. release SHA;
8. deployment verification where applicable.

This separation keeps V1.5 architecture, Stage 8 engineering and v1.3.8 release truth distinct.
