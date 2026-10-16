# Software Developer operation evidence matrix — 2026-10-16

## Purpose and evidence rules

This is the first bounded slice of the workforce operation-level evidence matrix, limited to `ai_software_developer`. It maps all 26 declared role operations to their declared tool binding, semantic dispatch, provider boundary, and the evidence currently available in source/tests/CI.

**Evidence labels**
- **Workspace-backed:** tenant-scoped workspace storage path exists and the W2 real-stack verifier exercises relevant lifecycle and isolation behavior.
- **Proposal/artifact only:** a governed request or proposal can be persisted; this is not evidence that a remote GitHub/production action occurred.
- **Provider-gated:** operation dispatches to the engineering provider boundary; behavior depends on operator configuration. `not_configured` is a deliberate fail-closed outcome, not successful execution.
- **Mocked provider test:** tests exercise provider behavior with mocked HTTP responses; not live external-provider certification.
- **Unbound:** role contract intentionally declares the operation approval-required but has no registered tool binding, so it cannot be executed through this role's current contract.
- **Source mapping only:** a mapping exists in declarations but no independent, operation-specific runtime acceptance is claimed here.

## Operation matrix

| Role operation | Class | Tool binding | Dispatch / current capability | Evidence and limitation |
|---|---|---|---|---|
| `workspace_read` | Routine | `workforce_workspace_read` | Tenant-scoped workspace read | W2 engineering E2E; do not infer all edge cases from the tool declaration alone. |
| `workspace_list` | Routine | `workforce_workspace_list` | Tenant-scoped workspace listing | W2 engineering E2E and workspace lifecycle checks. |
| `workspace_create_file` | Routine | `workforce_workspace_create_file` | Persists tenant-scoped workspace file | W2 E2E plus PR #1185 deletion lifecycle and PR #1187 edit/readback coverage. |
| `workspace_edit_file` | Routine | `workforce_workspace_edit_file` | Updates tenant-scoped workspace file | PR #1187 verifies edit readback and cross-tenant edit denial on the tested CI head. |
| `workspace_delete_file` | Routine | `workforce_workspace_delete_file` | Deletes tenant-owned workspace artifact | PR #1185 verifies cross-tenant denial, owner deletion, disappearance from listing, and read-after-delete failure. |
| `workspace_change_set` | Routine | `workforce_workspace_change_set` | Persists a proposed change-set artifact | W2 E2E exercises durable change sets; this is not an applied repository patch. |
| `workspace_test` | Routine | `workforce_workspace_test` | Engineering-provider dispatch | W2 verifier and provider tests expect `not_configured` unless an operator-configured implementation exists; do not claim tests were run by this operation. |
| `workspace_lint` | Routine | `workforce_workspace_lint` | Engineering-provider dispatch | Same fail-closed boundary as `workspace_test`; no lint execution is established by a proposal/artifact. |
| `workspace_build` | Routine | `workforce_workspace_build` | Engineering-provider dispatch | Same fail-closed boundary; no build execution is established by current evidence. |
| `git_pr_proposal` | Routine | `workforce_git_pr_proposal` | Proposal/artifact path; provider does not create a remote PR | Registry and semantic dispatch exist; no remote PR creation is claimed. |
| `ci_status` | Routine | `workforce_ci_status` | Provider supports read-only status lookup when configured and tenant-mapped | Unit tests cover mocked responses, invalid payloads, transport failures, and missing tenant mapping; no live-provider certification. |
| `health_check` | Routine | `workforce_health_check` | Provider boundary; no currently evidenced configured execution | Tool and dispatch exist, but the supported GitHub adapter operations are limited; result may be `not_configured`. |
| `implement_routine_fix` | Routine | `workforce_workspace_edit_file` | Alias to canonical workspace-edit tool operation | Declaration maps to the edit tool; this is not a separate implementation or separate runtime operation. |
| `write_tests` | Routine | `workforce_workspace_test` | Alias to canonical workspace-test tool operation | Declaration maps to the test tool; provider boundary remains fail-closed when unconfigured. |
| `prepare_integration` | Routine | `workforce_workspace_change_set` | Alias to change-set artifact operation | Preparation artifact only; no integration execution is implied. |
| `refactor_non_critical_code` | Routine | `workforce_workspace_change_set` | Alias to change-set artifact operation | Preparation artifact only; no independent refactor executor is evidenced. |
| `prepare_change_proposal` | Routine | `workforce_git_pr_proposal` | Alias to proposal/artifact operation | Does not establish a remote branch, commit, or pull request. |
| `git_branch` | Approval required | `workforce_git_branch` | Provider supports narrowly scoped branch creation with operator-configured tenant repository/token | Approval-gated; unit tests cover validation, identity/SHA checks, and ambiguous-write reconciliation. Tests use mocked HTTP; no live branch write is certified. |
| `git_commit_proposal` | Approval required | `workforce_git_commit_proposal` | Explicitly fails closed as `not_configured` | PR #1146 regression test asserts no execution; no Git commit is implemented by the current adapter. |
| `deploy_proposal` | Approval required | **None** | Intentionally unbound | PR #1189 regression test asserts the operation remains approval-required and unbound; no deployment capability is registered. |
| `rollback_proposal` | Approval required | **None** | Intentionally unbound | PR #1189 regression test asserts the operation remains approval-required and unbound; no rollback capability is registered. |
| `production_critical_change` | Approval required | **None** | Intentionally unbound | PR #1189 parameterized regression tests assert it remains approval-required, unbound, and fails closed if a binding is attempted. |
| `security_sensitive_change` | Approval required | **None** | Intentionally unbound | Same PR #1189 regression coverage; no runtime capability added. |
| `privileged_access_change` | Approval required | **None** | Intentionally unbound | Same PR #1189 regression coverage; no runtime capability added. |
| `material_resource_consumption` | Approval required | **None** | Intentionally unbound | Same PR #1189 regression coverage; no runtime capability added. |
| `irreversible_data_change` | Approval required | **None** | Intentionally unbound | Same PR #1189 regression coverage; no runtime capability added. |

## Cross-cutting governance evidence

- The role contract declares 17 routine and 9 approval-required operations. Its tool bindings are declarative capability mappings; they are not by themselves proof of independent operation implementations.
- Tool Registry entries bind the concrete workspace, CI, branch, proposal, health-check, and rollback-proposal tools to the engineering semantic dispatcher. Registry approval metadata and the role contract were source-checked for alignment in the preceding audit.
- The semantic dispatcher sends workspace read/list/create/edit/delete/change-set operations to tenant-scoped storage. Test/lint/build and Git/provider operations pass through the engineering provider boundary; unconfigured or unsupported operations fail closed.
- The canonical approval-resume path validates persisted approval identity against tenant, Run, tool, tool-call ID, approved status, and exact arguments before registry execution. PR #1189 separately protects all seven unimplemented Software Developer privileged operations (`deploy_proposal`, `rollback_proposal`, `production_critical_change`, `security_sensitive_change`, `privileged_access_change`, `material_resource_consumption`, `irreversible_data_change`) from accidental binding.
- Evidence includes source inspection and GitHub CI/test history. No fresh local pytest was run for this documentation checkpoint. Provider unit tests use mocked HTTP; no new live provider call, remote PR/commit, deployment, rollback, or production/customer outcome is claimed.

## Remaining work

1. Continue the same evidence mapping for the other workforce roles, prioritizing unimplemented or provider-dependent operations rather than tool-catalog breadth.
2. Add or link operation-specific positive and negative tests only where the matrix reveals a concrete evidence gap; avoid duplicate audits and speculative code changes.
3. Keep external-provider configuration and supervised live validation separate from local/CI progress. Keep the project progress indicators unchanged until the documented phase exit criteria are met.

**Progress accounting remains unchanged:** local operational readiness 78%; full product-scope coverage 46%; A0/A1/A2/A3/A4 = 100/30/100/0/0; actionable progress 77%. Certified release remains `v1.4.17` / `b403c0dcdea579e017738a6fdea138c2b1a2999c`.
