from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.edition_control import (
    list_reseller_support_escalations,
    list_vendor_support_escalations,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint,tenant_kind",
    [
        (list_vendor_support_escalations, "vendor"),
        (list_reseller_support_escalations, "reseller"),
    ],
)
async def test_support_inbox_lists_only_escalations_addressed_to_current_tenant(endpoint, tenant_kind):
    tenant_id = uuid4()
    source_tenant_id = uuid4()
    ticket = SimpleNamespace(
        id=uuid4(),
        from_tenant_id=source_tenant_id,
        to_tenant_id=tenant_id,
        status="open",
        subject="World room purchase question",
        description="Customer asks about a pending room purchase.",
    )
    result = SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [ticket]))
    db = AsyncMock()
    db.execute.return_value = result
    ctx = SimpleNamespace(tenant_id=tenant_id, tenant=SimpleNamespace(tenant_kind=tenant_kind))

    response = await endpoint(ctx, db)

    assert response.data[0].id == ticket.id
    assert response.data[0].to_tenant_id == tenant_id
    statement = str(db.execute.await_args.args[0])
    assert "support_escalations.to_tenant_id" in statement
    assert "support_escalations.created_at" in statement
