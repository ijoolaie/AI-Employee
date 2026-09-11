# Workflow Execution Hardening Audit — 2026-09-11

## Scope
Audit of stale `running` workflow execution after PR #477, focused on timeout/cancellation races across independent child `Run` commits.

## Finding P1 — post-child terminal-state bypass
`execute_workflow()` re-checks the parent before each step, but previously treated only `cancelled` as a stop condition. `RunService.execute_run()` can commit a child Run independently, releasing the parent row lock. The timeout sweep can then durably mark the parent `timed_out`; the stale workflow worker would observe that status and still enter the next step.

The same boundary existed in `_execute_parallel_branch()`: after a child Run commit, the branch worker did not re-check the parent before starting the next branch child.

## Fix
- Sequential workflow execution now proceeds past the per-step fence only while the parent status is exactly `running`.
- Parallel branch execution re-checks parent status and deadline before every child definition.
- Terminal `timed_out`, `cancelled`, `failed`, or `success` states therefore fail closed without starting another child execution.
- `running` remains non-retryable; this patch does not introduce blind stale-run replay.

## Remaining follow-up
A separate lease/recovery design is still required for workflows with no configured `max_runtime_seconds`, and for safe recovery of genuinely crashed `running` workers. Automatic replay must remain blocked until a durable execution lease/fence exists.

## Evidence
- Base main before this patch: `4cbcc933ab64e5ab88ce98bdf83013a24892c5d3`
- Tracking issue: #478
