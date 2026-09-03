"""Apply the central approval policy to the legacy Tool Registry at startup.

This compatibility layer keeps the existing registry data model intact while
making the centralized policy authoritative for every execution path. It is
imported by the services package, which is loaded by the Run execution service.
"""

from app.ai.tool_registry import registry
from app.services.tool_approval_policy import requires_approval


for _tool in registry.list():
    if requires_approval(_tool.name, _tool.requires_approval):
        # RegisteredTool is intentionally frozen; changing the effective flag
        # once during application bootstrap prevents request-time mutation.
        object.__setattr__(_tool, "requires_approval", True)
