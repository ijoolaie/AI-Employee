"""Shared pytest compatibility helpers for service unit doubles."""

import pytest

from app.services.unified_execution import UnifiedExecutionService


@pytest.fixture(autouse=True)
def allow_lightweight_dispatch_db_doubles(monkeypatch):
    """Keep legacy unit doubles usable without weakening production sessions."""
    original = UnifiedExecutionService._locked_work_item

    async def locked_or_passthrough(service, work_item):
        if not hasattr(service.db, "execute"):
            return work_item
        return await original(service, work_item)

    monkeypatch.setattr(UnifiedExecutionService, "_locked_work_item", locked_or_passthrough)
