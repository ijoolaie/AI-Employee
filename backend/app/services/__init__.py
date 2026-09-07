# Services package

# Import the central AI side-effect approval policy at package bootstrap so the
# Tool Registry cannot accidentally execute mandatory-approval tools without
# the Human-in-the-loop gate.
from app.services import tool_approval_policy_bootstrap as _tool_approval_policy_bootstrap  # noqa: F401,E402

# Install the Agent governance context around the canonical Run execution path.
# Ordinary Employee Runs remain unchanged; Agent Runs acquire a tenant-scoped
# AgentInstance context before any ToolRegistry execution.
from app.services import agent_run_governance_bootstrap as _agent_run_governance_bootstrap  # noqa: F401,E402
