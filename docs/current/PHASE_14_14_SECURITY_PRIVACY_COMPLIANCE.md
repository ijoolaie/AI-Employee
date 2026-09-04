# Phase 14.14 — Security, Privacy & Compliance Engineering Extensions

**Status:** Engineering implementation / evidence gate in progress.

This stage strengthens the repository security boundary before the final external-production gate. It does not represent a penetration test, SOC 2/ISO certification, GDPR certification, or production security attestation.

## Threat-model refresh

| Asset / boundary | Threat | Engineering control | Evidence |
| --- | --- | --- | --- |
| Tenant data | Cross-tenant read/write through forged identifiers | Authenticated tenant context plus tenant-scoped queries and RBAC | Regression tests + CI |
| Tool execution | Prompt/provider output invokes an unauthorized or dangerous tool | Immutable allowed-tool guardrail, explicit permission, JSON-schema validation, approval gate for side effects | Tool registry tests + CI |
| Side-effecting tools | External action occurs without human authorization | Registered side-effecting tools must declare `requires_approval=True` and `run.execute` | Registration invariant + tests |
| API keys | Stolen/scoped key reaches an unauthorized capability | Explicit API-key scopes checked before permission evaluation | Existing auth tests + CI |
| Privacy requests | Export/delete crosses tenant boundary | Privacy endpoints require dedicated permissions and services query by tenant | Existing privacy implementation + regression coverage |
| Sensitive evidence | Secrets/customer data copied into repository artifacts | Evidence artifacts are explicitly non-secret and external production evidence stays outside Git | Security gate + release policy |
| Dependencies | Vulnerable package reaches release candidate | Locked direct dependencies plus automated vulnerability scan | CI dependency scan |

## Privacy and retention boundary

Customer export is tenant-scoped and returns customer, conversation metadata/messages and related orders. Customer deletion is intentionally an anonymization/deactivation operation: customer identifiers/contact fields are removed, conversation ownership is detached, and the privacy action is audited.

Retention policy is an operational control, not an implicit deletion guarantee. Production retention periods, legal holds, backup lifecycle and object-storage lifecycle must be configured and evidenced in the target environment. Repository CI must not claim that production data has been purged merely because the privacy API tests pass.

## Compliance-control mapping

| Control family | Engineering mapping | External evidence still required |
| --- | --- | --- |
| Access control | TenantContext, RBAC permissions, API-key scopes, approval permissions | Deployed identity configuration, role review and access recertification |
| Data minimization | Privacy export/delete boundaries and anonymization | Target retention schedule, legal-hold process and deletion verification |
| Auditability | Durable audit records for security-sensitive actions | Production audit retention, access review and monitoring evidence |
| Change security | CodeQL, architecture/release gates, dependency scanning | Organization change-management evidence |
| Incident response | Existing incident-response baseline and security reporting policy | Production incident exercises, contacts and response records |
| Business continuity | Backup/restore and recovery controls | Target RPO/RTO evidence and restore drill |

## Pentest-ready scope / runbook

1. Freeze the exact release SHA and deployment image digests under test.
2. Create isolated test tenants with representative non-production data only.
3. Test authentication/session invalidation, API-key scope escalation and RBAC bypass attempts.
4. Test cross-tenant object access for customers, files, runs, workflows, audit records and privacy requests.
5. Test tool abuse paths: unauthorized tools, side-effecting tools without approval, malformed tool arguments and prompt/provider output injection into tool selection.
6. Test webhook replay/signature handling, rate limits, payload-size controls and SSRF-sensitive integration inputs where applicable.
7. Validate privacy export/delete behavior, retention boundaries and backup copies without using real customer data.
8. Record findings with severity, affected component, exact build identity, reproduction steps and remediation status.
9. Re-test fixes against the same release identity or a new immutable candidate.
10. Keep the final pentest report external to the repository unless it contains only a sanitized, non-sensitive summary.

## Evidence boundary

CI and repository tests establish engineering controls for the checked commit. They cannot prove external production configuration, live SLOs, independent penetration testing, legal compliance, customer acceptance or certification. Those remain Stage 7 external evidence.
