"""Real-stack W10 governed commercial commitment certification.

Uses the existing W10 fixture builder, moves its CRM deal from qualified to
proposal, then executes the approval-gated commercial commitment through the
operator-selected contract-test payment provider. No external payment occurs.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import AsyncSessionLocal
from app.models.tool_approval import ToolApprovalRequest
from app.services.modules import sales_service if False else None
