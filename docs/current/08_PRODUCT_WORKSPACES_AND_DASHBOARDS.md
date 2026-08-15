# Product Workspaces and Dashboard Architecture

## Purpose

The product now separates four UX surfaces while keeping a single underlying tenant/employee/conversation architecture.

## 1. Platform Admin

**Audience:** SaaS owner/operator.

Route: `/admin`

Responsibilities:
- Tenant management
- Platform validation
- Operational control-plane functions
- System-level administration

This surface is isolated from normal tenant operations.

## 2. Business Dashboard

**Audience:** store/business owner and authorized staff.

Route: `/dashboard`

Purpose:
- Revenue and operational overview
- Orders and sales
- Business analytics
- Billing and usage
- High-level health of the tenant

The Business Dashboard answers: **"How is my business doing?"**

## 3. AI Workspace

**Audience:** business users responsible for AI Employees.

Route: `/workspace`

Purpose:
- Create and configure AI Employees
- Manage employee versions
- Manage knowledge and memory
- Review customer conversations
- Configure workflows and tools
- Publish customer-facing channels

The AI Workspace answers: **"How are my AI Employees performing and how do I improve them?"**

## 4. Customer Experience

**Audience:** end customers of the tenant, not SaaS users.

Public route: `/chat/[publicKey]`

The customer does not need a SaaS account. A public channel resolves to a tenant-owned employee and creates a tenant-scoped conversation. Messages are then processed through the existing Run Service, AI Gateway, RAG, Memory, Tool Registry and approval controls.

The customer experience should remain intentionally simple: chat first, with optional product/order context.

## Navigation model

```text
Platform Admin
  └── /admin

Tenant / Business
  ├── Business Dashboard
  │    ├── Orders
  │    ├── Sales
  │    ├── Analytics
  │    └── Billing
  │
  └── AI Workspace
       ├── AI Employees
       ├── Customer Conversations
       ├── Knowledge Base
       ├── Memory
       ├── Workflows
       └── Developer / Integrations

End Customer
  └── Public Customer Chat
       └── Conversation → Run → Employee
```

## Product terminology

Do not call the public customer chat a "dashboard". It is a **Customer Experience / Channel**.

The recommended product vocabulary is:
- Platform Admin
- Business Dashboard
- AI Workspace
- Customer Experience

This distinction prevents B2B tenant controls and B2C customer interactions from being mixed in the UI.

## Frontend implementation

The tenant frontend now exposes:
- `/dashboard` — Business Dashboard
- `/workspace` — AI Workspace landing page
- `/employees` — AI Employee management and publishing
- `/channels` — customer channel management, public chat links and website embed snippets
- `/conversations` — customer conversation monitoring
- `/chat/[publicKey]` — public B2C customer chat
- `/widget.js?channel=<publicKey>` — embeddable website widget loader

The `/channels` surface is the recommended place for a tenant operator to publish and copy customer-facing entry points. It uses the existing customer-channel APIs and does not introduce a second AI execution path.
