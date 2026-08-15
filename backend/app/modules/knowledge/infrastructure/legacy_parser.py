from __future__ import annotations
from typing import Any

class LegacyDocumentParser:
    """Adapter for the existing RC8 document/RAG ingestion implementation."""
    def __init__(self, legacy_service: Any) -> None:
        self.legacy_service = legacy_service

    async def parse(self, source: str) -> list[dict[str, Any]]:
        result = await self.legacy_service.parse(source)
        return result if isinstance(result, list) else [{"text": str(result), "metadata": {}}]
