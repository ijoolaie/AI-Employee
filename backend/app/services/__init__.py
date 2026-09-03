# Services package

# Import the central AI side-effect approval policy at package bootstrap so the
# Tool Registry cannot accidentally execute mandatory-approval tools without
# the Human-in-the-loop gate.
from app.services import tool_approval_policy_bootstrap as _tool_approval_policy_bootstrap  # noqa: F401,E402
