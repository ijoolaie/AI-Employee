"""Shared pytest compatibility helpers for lightweight service unit doubles."""

import pytest

from app.services.unified_execution import UnifiedExecutionService


@pytest.fixture(autouse=True)
def allow_lightweight_dispatch_db_doubles(monkeypatch):
    """Keep legacy unit doubles usable without changing production session behavior."""
    claim = UnifiedExecutionService._claim_dispatch
    finalize = UnifiedExecutionService._finalize_dispatch

    async def claim_or_passthrough(service, work_item):
        if not hasattr(service.db, "execute"):
            return work_item
        return await claim(service, work_item)

    async def finalize_or_passthrough(service, work_item, output, status_value):
        if not hasattr(service.db, "execute"):
            work_item.output_data = output
            work_item.status = status_value
            return work_item
        return await finalize(service, work_item, output, status_value)

    monkeypatch.setattr(UnifiedExecutionService, "_claim_dispatch", claim_or_passthrough)
    monkeypatch.setattr(UnifiedExecutionService, "_finalize_dispatch", finalize_or_passthrough)
