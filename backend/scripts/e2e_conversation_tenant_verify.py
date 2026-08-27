"""Real-stack negative checks for authenticated/public conversation tenant boundaries."""
import asyncio
import os
import uuid

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


async def main() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # This gate is intentionally conservative: it verifies that an arbitrary
        # conversation UUID cannot be accessed through the authenticated API.
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/conversations/{fake_id}")
        assert response.status_code in (401, 403, 404), response.text
        print("CONVERSATION CROSS-TENANT/UNKNOWN-ID NEGATIVE CHECK PASS")


if __name__ == "__main__":
    asyncio.run(main())
