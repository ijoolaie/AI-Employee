# User Guide — First Use

## 1. Create an account

Open the frontend and choose **Register**.

Create:
- organization/tenant name
- tenant slug
- user email
- password
- full name

Then log in.

## 2. Create an AI Employee

Go to **Employees** → **New Employee**.

Start with:
- a clear name;
- a unique slug;
- a short system prompt;
- no autonomous tools initially.

Example objective:

> You are a concise sales assistant. Answer the customer's question using the supplied context. If information is missing, say that you do not know.

Save the employee.

## 3. Run the employee

Open the employee and start a Run with a simple JSON input, for example:

```json
{
  "message": "Write a two-sentence reply to a customer asking about delivery time."
}
```

Watch the Run page until it reaches a terminal state.

## 4. Read a Run

A successful Run should expose its output and execution metadata. A failed Run should expose a safe error state without leaking secrets.

Use **Traces** / **Developer** for operational inspection when your account has permission.

## 5. Files

Use **Files** to upload tenant-scoped documents.

Do not upload real secrets or credentials. For the first test use a tiny CSV, TXT, PDF or DOCX.

## 6. Knowledge and Memory

Use **Knowledge** for information intended to be retrieved as context.

Use **Memory** for durable tenant/user/employee context that should have an explicit lifecycle.

Do not treat Memory as an unrestricted document store.

## 7. Workflows

Create workflows only after simple Runs are working.

A safe first workflow:
1. trigger manually;
2. execute one AI step;
3. save result;
4. stop.

Then add:
- approval;
- retries;
- timeout;
- schedule;
- external events.

## 8. Business modules

Recommended order:
1. Orders
2. Sales / Deals
3. Invoices
4. Billing

Test each independently before combining them.

## 9. Developer/Admin

Developer tools are for traces, metrics, API keys, webhooks and operational state.

Admin is for platform-level tenant/validation functions. Never grant platform-admin privileges simply because a user is a tenant administrator.

## 10. Production usage

Before real users:
- replace development secrets;
- configure HTTPS;
- configure a managed PostgreSQL/Redis strategy;
- configure persistent object storage;
- configure email;
- configure AI provider credentials if needed;
- configure Stripe only if billing is enabled;
- configure monitoring;
- run the full release checklist.
