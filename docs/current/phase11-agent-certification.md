# Phase 11 Agent Real-Stack Certification

This acceptance gate provisions a tenant-scoped AgentDefinition, AgentInstance, AgentRuntimeBinding and EmployeeVersion in the certification PostgreSQL database, creates an Agent WorkItem, assigns it through the WorkItem API, dispatches it through UnifiedExecutionService, and verifies that the resulting Run is correlated to the same tenant and resolved EmployeeVersion.

The gate is wired into `.github/workflows/production-certification.yml` as `Agent WorkItem real-stack runtime binding`.

It is not considered VERIFIED until a Production Certification GitHub Actions run executes the gate successfully.
