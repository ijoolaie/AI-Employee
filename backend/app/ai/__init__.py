"""AI package bootstrap.

Importing the AI package installs the Agent ToolRegistry governance hook so
there is no alternate ungoverned registry entry point based on import order.
"""

# Keep the registry import first: the governance module wraps this canonical
# registry instance and therefore remains safe from a circular import.
from app.ai import tool_registry as _tool_registry  # noqa: F401
from app.services import agent_tool_governance as _agent_tool_governance  # noqa: F401
