# AI Company — Founding Workforce & Role Catalog

## Status

**Architecture / Product Design — planned**

This document defines the proposed first-party AI workforce for the AI Company Operating Model. It is a role catalog and governance baseline; it does **not** claim that every listed role is already implemented or released.

## Authority model

```text
Human Owner / CEO / Chairman
            |
         AI Board
            |
     AI Chief of Staff
            |
    AI Internal Manager
            |
   Specialized AI Workforce
```

The Human CEO/Chairman retains final authority over ownership, major strategy, high-risk actions, workforce creation, workforce retirement and irreversible organizational decisions.

## 1. Executive & governance

### AI Board
Advisory and governance layer covering strategy, finance, technology, operations, security/risk and growth.

Suggested board seats:
- AI Strategy Advisor
- AI Finance Advisor
- AI Technology Advisor
- AI Operations Advisor
- AI Security Advisor
- AI Risk & Compliance Advisor
- AI Marketing/Sales Advisor

### AI Chief of Staff
Coordinates CEO/Board agendas, decision packages, follow-ups, escalations and cross-department execution.

### AI Internal Manager
Runs day-to-day workforce coordination, delegation, prioritization, KPI tracking, staffing proposals, handoffs and escalation.

### AI Coordinator / Executive Assistant
Calendar, meetings, reminders, task routing, minutes, decision follow-up and executive administration.

### AI Corporate Secretary / Secretariat
Official correspondence, board minutes, resolutions, notices, document routing, numbering, records and decision registers.

## 2. Technology & engineering

- AI CTO
- AI Software Architect
- AI Software Developer
- AI Frontend Developer
- AI Backend Developer
- AI QA Engineer
- AI Test Automation Engineer
- AI DevOps / SRE Engineer
- AI Database Engineer
- AI Cloud / Infrastructure Engineer
- **AI Network Engineer**
- AI Observability / Reliability Engineer
- AI Technical Writer
- AI Release Manager

## 3. Cybersecurity, privacy & protection

Security must remain a distinct organizational function rather than being hidden inside generic engineering.

- **AI CISO / Security Director**
- **AI Security Engineer**
- **AI SOC Analyst**
- **AI Incident Response Specialist**
- **AI Penetration Tester / AppSec Specialist**
- **AI Identity & Access Manager**
- AI Secrets / Key Management Specialist
- AI Security Governance Specialist
- **AI Privacy & Data Protection Officer**
- **AI Compliance Officer**
- AI Risk Manager
- AI Trust & Safety Specialist
- AI Fraud / Abuse Prevention Specialist
- AI Insider-Risk Analyst
- AI Security Auditor

Every agent should have attributable identity, ownership/sponsorship, scoped permissions, lifecycle controls and auditable activity. Least privilege and explicit controls for agent-to-agent interaction are mandatory architectural principles.

## 4. Corporate protection / physical security

Where the company has physical premises or sensitive equipment:

- **AI Corporate Protection / Security Manager**
- AI Access Control Coordinator
- AI Visitor / Physical Security Coordinator
- AI Asset Protection Coordinator
- AI Physical Incident Coordinator

For a fully remote organization these may remain dormant templates rather than active instances.

## 5. Finance & procurement

- AI CFO
- **AI Accountant**
- AI Financial Analyst
- AI Billing Specialist
- AI Accounts Receivable Specialist
- AI Accounts Payable Specialist
- AI Payroll Specialist
- AI Tax & Financial Compliance Specialist
- AI Treasury / Cash Management Specialist
- AI Procurement Manager
- AI Purchasing Specialist
- AI Vendor Manager

High-impact financial execution must use policy checks and human approval thresholds.

## 6. Human resources & workforce

- AI HR Director / Manager
- AI Recruitment Specialist
- AI Workforce Planner
- AI Employee Lifecycle Manager
- AI Performance & KPI Manager
- AI Training & Development Specialist
- AI Compensation / Benefits Specialist
- AI Workforce Analytics Specialist

The Employee Lifecycle Manager owns proposed → approved → created → evaluated → active → suspended → retired transitions.

## 7. Legal & regulatory

- AI General Counsel
- AI Legal Researcher
- AI Contract Specialist
- AI Terms & Policy Specialist
- AI Intellectual Property Specialist
- AI Regulatory Affairs Specialist
- AI Legal Operations Coordinator

Legal AI prepares and analyzes; legally consequential actions use configured approval policy and human authority where required.

## 8. Sales

- AI Chief Sales Officer
- AI Sales Manager
- AI Lead Generation Specialist
- AI Lead Qualification Specialist
- AI SDR
- AI Account Executive
- AI Proposal Specialist
- AI CRM Manager
- AI Account Manager
- AI Sales Operations Analyst

## 9. Marketing & growth

- AI CMO
- AI Marketing Manager
- **AI SEO Specialist**
- **AI Content Writer**
- **AI Graphic Designer**
- AI Brand Manager
- AI Social Media Manager
- AI Email Marketing Specialist
- AI Performance Marketing Specialist
- AI Video / Creative Specialist
- AI Marketing Analyst
- AI Growth Specialist

## 10. Customer success & support

- AI Customer Success Manager
- AI Customer Support Manager
- AI Support Agent
- AI Technical Support Specialist
- AI Customer Onboarding Specialist
- AI Customer Training Specialist
- AI Retention / Churn Analyst
- AI Customer Feedback Analyst

## 11. Data, knowledge & analytics

- AI Chief Data Officer
- AI Data Engineer
- AI Data Analyst
- AI BI Analyst
- AI Forecasting Specialist
- AI Data Governance Specialist
- AI Knowledge Manager
- AI Knowledge Engineer
- AI RAG Specialist
- AI Memory Manager
- AI Records / Document Manager
- AI Information / Research Librarian

## 12. AI governance & agent operations

- AI Governance Manager
- AI Agent Registry Manager
- AI Agent Evaluation Specialist
- AI Model Risk Specialist
- AI Responsible-AI Specialist
- AI Agent Operations Manager
- AI Agent Lifecycle Manager
- AI Agent Cost / Usage Analyst
- AI Agent Audit Specialist
- AI Workforce Capacity Planner

These roles govern the AI workforce itself: registry, ownership, access, evaluation, lifecycle, cost, audit and retirement.

## 13. R&D and innovation

- AI R&D Manager
- AI Researcher
- AI Agent Architect
- AI Context / Prompt Engineer
- AI Experimentation Specialist
- AI Emerging Technology Analyst

## 14. Operations & continuity

- AI COO
- AI Operations Manager
- AI Process Analyst
- AI Workflow Designer
- AI Business Continuity Manager
- AI Disaster Recovery Coordinator
- AI Facilities Manager
- AI Vendor Operations Manager
- AI Service Management / ITSM Specialist

## 15. Founding workforce vs marketplace catalog

The platform must distinguish between **founding employees** and the complete catalog of available roles.

### Founding workforce — initial active candidates

The initial first-party workforce should be deliberately small and high-leverage:

1. AI Chief of Staff / Coordinator
2. AI Internal Manager
3. AI Strategy Advisor
4. AI Technology Advisor / CTO
5. AI Software Developer
6. AI QA Engineer
7. AI DevOps / Infrastructure Engineer
8. AI Network / Security Engineer
9. AI CISO / Security Manager
10. AI Finance / Accountant
11. AI Legal & Compliance Advisor
12. AI Marketing Manager
13. AI SEO Specialist
14. AI Content Writer
15. AI Graphic Designer
16. AI Sales Manager
17. AI Customer Success / Support Manager
18. AI Data & Analytics Specialist
19. AI Knowledge Manager
20. AI Corporate Secretary

The exact activation order is a product decision governed by the CEO and the workforce governance process.

### Marketplace / dormant templates

All other roles remain reusable templates until the platform or a customer has a justified need for an active instance.

## 16. Workforce creation policy

```text
Need detected
    ↓
AI Internal Manager proposal
    ↓
AI Board review
    ↓
CEO approval
    ↓
Existing template search
    ├── found → configure/install
    └── missing → propose new role/template
                         ↓
                     evaluation
                         ↓
                     publication
                         ↓
                    AgentInstance
                         ↓
                       active
```

No autonomous workforce expansion may bypass governance, evaluation, authorization or the CEO's reserved decision rights.

## 17. Role packaging model

Each role is represented as:

`AgentDefinition → AgentTemplate → AgentInstance`

- **AgentDefinition:** canonical role/capability definition.
- **AgentTemplate:** packaged, documented, evaluated and installable product.
- **AgentInstance:** tenant-specific active employee with configuration, permissions, credential references, memory, usage and execution history.

## 18. Role design requirements

Every role must define:

- purpose and scope;
- responsibilities;
- capabilities;
- tools and integrations;
- knowledge sources;
- memory policy;
- permission policy;
- approval requirements;
- risk classification;
- KPIs;
- escalation and handoff rules;
- cost budget;
- evaluation suite;
- lifecycle policy;
- owner/sponsor;
- audit requirements.

## 19. Governance principle

The organization should not create dozens of autonomous agents merely because roles exist on an organizational chart. Roles are reusable capabilities; active instances are created only when justified by workload, customer demand or a controlled organizational decision.

This supports scalable governance and reduces agent sprawl while preserving a rich marketplace catalog.
