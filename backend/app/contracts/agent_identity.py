"""Contracts for governed agent identity lifecycle."""

from __future__ import annotations

from enum import Enum


class AgentIdentityLifecycleAction(str, Enum):
    CREATE = "create"
    ACTIVATE = "activate"
    SUSPEND = "suspend"
    REVOKE = "revoke"
    ROTATE = "rotate"
