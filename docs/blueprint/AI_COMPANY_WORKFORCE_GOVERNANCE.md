# AI Company Workforce Governance & Operating Model

## Status

**Architecture / Product Design — Stage 8 foundation**

This document turns the workforce role catalog into an operational governance model. It does not claim that the roles or controls are implemented in the current release.

## 1. Authority hierarchy

```text
Human Owner / CEO / Chairman
        |
     AI Board
        |
 AI Chief of Staff
        |
 AI Internal Manager
        |
 Specialized AI Workforce / Teams
```

The CEO/Chairman retains final authority over ownership, major strategy, high-risk actions, workforce creation/retirement, irreversible decisions and exceptions to governance policy.

## 2. Workforce layers

### Governance
- CEO / Chairman
- AI Board
- AI Chief of Staff

### Management
- AI Chief of Staff
- AI Internal Manager
- Domain Managers / Directors
- Workforce Planner

### AI Internal Manager operating mandate

The Internal Manager is the operational manager of the specialized AI workforce. It is not merely another task-oriented assistant.

It is responsible for:

- supervising active AI employees and their workload;
- assigning and reprioritizing work within authorized boundaries;
- monitoring KPI, SLA, queue, quality, failure and escalation signals;
- coordinating handoffs between employees and departments;
- identifying capability or capacity gaps;
- preparing workforce proposals for the CEO;
- preparing hiring/provisioning requests;
- preparing retirement/removal requests;
- preparing transfer/reassignment requests;
- preparing replacement requests;
- preparing urgent operational budget requests;
- producing financial estimates for proposed operational actions;
- reporting workforce status, performance, utilization and cost to the CEO;
- escalating incidents, exceptions and unresolved cross-team conflicts.

The Internal Manager uses **CEO approval by default**. No workforce, financial or material operational action is assumed to be pre-authorized.

The CEO may explicitly delegate a bounded subset of routine authority to the Internal Manager. Delegation must define scope, duration, affected employees/teams, spending/resource limits, risk tier and revocation conditions, and must be auditable.

Delegated authority may cover routine non-financial, non-critical and reversible operations such as task assignment, reprioritization, handoffs, workload balancing and other low-risk workforce coordination. It does not authorize financial commitments, purchases, material resource consumption, high-impact hiring/retirement, privileged/security changes, legal commitments, production-critical changes or irreversible actions unless the CEO explicitly and separately authorizes them under policy.

### Immediate next workforce roles

1. **AI Marketing & Advertising Manager** — owns marketing strategy, campaigns, channel planning, content coordination, advertising proposals, campaign analytics and growth execution. Material ad spend, paid campaigns and contractual commitments require CEO/authorized-human approval.
2. **AI Graphic Designer** — creates and adapts brand assets, advertising creatives, social graphics, presentations and other visual materials. Routine production may be delegated; paid asset procurement, licensing commitments or material spend require approval.
3. **AI Software Developer** — implements approved product changes, fixes, integrations, tests and engineering tasks. Routine low-risk work may be delegated; production-critical, security-sensitive or material-resource actions remain approval-gated.
4. **AI Trader** — researches markets, prepares trading plans, analyzes risk and may prepare or stage orders within explicit limits. Actual financial execution, capital allocation, leverage, withdrawals or other material financial actions require CEO/authorized-human approval.

These roles are candidates for the next governed implementation slice; their listing here does not claim that active instances already exist.

### Specialist workforce
Technology, Security, Network, Finance, HR, Legal, Sales, Marketing, Customer Success, Data, Knowledge, Operations, Governance, R&D and Corporate Secretariat roles are defined in `AI_COMPANY_FOUNDING_WORKFORCE.md`.

## 3. Security and protection separation

Security is not a single generic employee. The model separates:

- CISO / Security Director — accountable for security strategy and risk.
- Security Engineering — preventive technical controls.
- SOC — monitoring and detection.
- Incident Response — containment, investigation and recovery.
- IAM — identity, authorization and access reviews.
- AppSec / Penetration Testing — adversarial validation.
- Privacy / Data Protection — personal-data controls.
- Compliance / Risk — policy and regulatory controls.
- Corporate Protection — physical security where premises/assets require it.

Agent identities must be attributable, scoped, auditable and governed throughout their lifecycle. No agent should exist without an accountable human sponsor/owner for lifecycle and access decisions.

## 4. Corporate Secretariat

The Corporate Secretary / Secretariat is responsible for:

- Board agendas and minutes;
- resolutions and decision registers;
- official correspondence;
- notices and internal directives;
- document routing and numbering;
- archival and records coordination;
- follow-up of formal decisions.

This function is separate from the AI Coordinator. The Coordinator manages operational scheduling and execution; the Secretariat maintains the formal corporate record.

## 5. Decision rights

Use a single accountable owner for each material decision.

| Decision | Responsible | Accountable | Consulted |
|---|---|---|---|
| Company strategy | AI Board | CEO | Chief of Staff |
| Workforce proposal | Internal Manager | CEO | AI Board |
| Routine low-risk agent activation | Workforce Manager | Internal Manager | Security/Governance |
| New role/template | Internal Manager | CEO | AI Board, Governance, Domain Owner |
| Delegated routine workforce operation | Internal Manager | Internal Manager within explicit delegation | CEO / Governance |
| Financial or material resource action | Internal Manager | CEO / authorized human | Finance, Risk |
| Trader financial execution | Trader | CEO / authorized human | Finance, Risk, Internal Manager |
| Marketing campaign with material spend | Marketing Manager | CEO / authorized human | Finance, Internal Manager |
| Production-critical engineering change | Software Developer | CEO / authorized authority | Technology, Security, Internal Manager |
| High-risk agent release | Agent Owner | CEO / designated authority | Security, Risk, Compliance |
| Production incident | Incident Response | CISO / Operations | CTO, Internal Manager |
| Security exception | Security/Risk | CISO | CEO |
| Financial action above threshold | Finance Agent | CEO / authorized human | CFO, Risk |
| Agent retirement | Agent Lifecycle Manager | Internal Manager / CEO for critical agents | Security, Domain Owner |

## 6. RACI requirement

Every important workforce lifecycle operation must have exactly one Accountable role. Multiple Responsible roles are allowed; multiple Accountable roles are not.

Required RACI domains:

- role proposal;
- risk classification;
- security review;
- evaluation;
- publication;
- installation;
- permission grant;
- production activation;
- incident response;
- access review;
- suspension;
- retirement;
- template versioning;
- customer installation;
- cost review.

## 7. Agent identity and sponsorship

Every active AgentInstance must have:

- unique identity;
- AgentDefinition reference;
- AgentTemplate/version reference where applicable;
- tenant scope;
- accountable human sponsor/owner;
- permission set;
- credential references (never raw secrets in prompts or model context);
- risk tier;
- lifecycle state;
- audit stream;
- usage/cost attribution.

A sponsor is accountable for lifecycle and access decisions. Technical ownership may be assigned separately for operations and incident response.

## 8. Risk tiers and autonomy

### Tier 0 — Read / assist
Examples: research, summarization, internal drafting.

- broad automation allowed within tenant permissions;
- no irreversible external action.

### Tier 1 — Low-impact execution
Examples: internal task creation, content drafts, non-sensitive workflow updates.

- policy-controlled automation;
- audit required.

### Tier 2 — External/customer impact
Examples: customer messages, proposals, publishing content, support actions.

- explicit scope and disclosure rules;
- escalation for ambiguity;
- stronger evaluation requirements.

### Tier 3 — Financial/legal/security impact
Examples: payments, contractual commitments, security changes, privileged access.

- prepare → policy check → human approval → execute;
- complete audit trail.

### Tier 4 — Critical / irreversible
Examples: destructive operations, production security changes with material blast radius, irreversible organizational actions.

- human approval mandatory;
- dual control where policy requires it;
- bounded execution and rollback/recovery plan.

## 9. Workforce lifecycle

```text
Need detected
    ↓
Proposal
    ↓
Board review
    ↓
CEO approval
    ↓
Template selection / new template design
    ↓
Security + risk review
    ↓
Evaluation suite
    ↓
Publication
    ↓
Installation
    ↓
AgentInstance
    ↓
Active
    ↓
Monitor / Evaluate / Review access
    ↓
Suspend / Upgrade / Replace / Retire
```

No autonomous workforce expansion may bypass the lifecycle.

## 10. Operational controls

Every active employee/agent should expose:

- health;
- current workload;
- queue;
- pending approvals;
- current permissions;
- recent actions;
- cost/usage;
- evaluation score;
- incidents;
- escalation state;
- version and template lineage.

Critical agents require monitoring, alerting, incident ownership and defined recovery procedures.

## 11. Workforce capacity management

The Internal Manager and Workforce Planner should continuously evaluate:

- workload volume;
- queue latency;
- SLA performance;
- capability coverage;
- utilization;
- cost per outcome;
- failure/escalation rate;
- customer demand;
- duplicate/overlapping roles.

A new role is justified by a measurable capability gap, demand or risk requirement—not merely by organizational aesthetics.

## 12. Agent sprawl controls

The platform must prevent uncontrolled growth of active agents.

Controls include:

- centralized registry;
- unique owner/sponsor;
- template lineage;
- duplicate-role detection;
- inactivity review;
- expiration/access review;
- cost budgets;
- automatic suspension policies where approved;
- retirement workflow;
- audit history.

## 13. Evaluation gate

Before publication or material version change, a role/template must pass the applicable evaluation suite:

- functional behavior;
- authorization/RBAC;
- tenant isolation;
- tool permissions;
- prompt/context safety;
- memory isolation;
- handoff behavior;
- approval behavior;
- failure handling;
- cost limits;
- observability;
- regression tests.

External-facing or high-impact agents require stronger responsible-AI, security and compliance review.

## 14. Human-in-the-loop

Human approval is mandatory where actions are consequential, hard to reverse, financially material, legally binding, security-sensitive or otherwise classified as requiring approval by policy.

The approval screen must provide enough context for the reviewer to make a decision without reconstructing the entire execution history.

## 15. Customer-facing workforce

The same architecture powers the customer marketplace:

`AgentDefinition → AgentTemplate → AgentInstance`

Customer installations must remain tenant-scoped and inherit the template's declared capability, risk, tool, evaluation and governance metadata. Customer administrators may configure within policy boundaries but cannot bypass platform safety controls.

## 16. Governance UX requirements

Stage 8 should expose:

- Workforce roster;
- Agent Registry;
- Board decisions;
- Workforce proposals;
- approvals;
- role/template catalog;
- team composition;
- agent health;
- permission/access reviews;
- cost/usage;
- incidents;
- evaluations;
- lifecycle actions;
- audit trail.

## 17. Exit criteria for Stage 8

Stage 8 is complete only when:

1. authority and decision rights are implemented;
2. founding workforce roles are represented by governed definitions;
3. AgentDefinition/Template/Instance separation is enforced;
4. identity, sponsorship and permissions are enforced;
5. risk tiers and autonomy limits are implemented;
6. workforce lifecycle is executable;
7. security/privacy/compliance gates are integrated;
8. evaluation gates exist;
9. customer installation is tenant-safe;
10. registry, audit, cost and health views are operational;
11. workforce expansion and retirement are governed;
12. evidence demonstrates the controls on the relevant release SHA.

Documentation alone cannot satisfy these exit criteria.
