"""Central, fail-closed approval policy for AI tool side effects.

The Tool Registry remains the execution boundary. This module defines the
business-risk classification once so high-risk mutations cannot accidentally
become approval-free because a registration omitted its local flag.
"""

from __future__ import annotations

from typing import Final

# Financial mutations and externally-visible mutations always require a human
# approval. Read-only tools and local artifact generation remain outside this
# mandatory gate unless their registry definition explicitly requires approval.
MANDATORY_APPROVAL_TOOLS: Final[frozenset[str]] = frozenset(
    {
        "create_order",
        "create_invoice",
        "update_order_status",
        "update_invoice_status",
        "create_deal",
        "update_deal_stage",
        "link_order_invoice",
        "send_email",
    }
)


def requires_approval(tool_name: str, explicitly_required: bool = False) -> bool:
    """Return the effective approval requirement for a registered tool.

    Explicit registration requirements can only make the policy stricter; they
    can never disable a mandatory high-risk requirement.
    """

    return explicitly_required or tool_name in MANDATORY_APPROVAL_TOOLS
