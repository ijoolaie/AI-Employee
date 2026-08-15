from __future__ import annotations
from typing import Any

class LegacyCustomerIdentityResolver:
    """Adapter for the existing RC8 CRM/customer lookup implementation."""
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service

    async def resolve(self, email: str | None, external_id: str | None):
        result = await self.legacy_service.resolve(email=email, external_id=external_id)
        return result if isinstance(result, dict) else None
