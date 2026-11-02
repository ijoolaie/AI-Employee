from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError
from app.services import edition_service, license_service


def _result(value):
    return SimpleNamespace(scalar_one_or_none=lambda: value)


@pytest.mark.asyncio
async def test_vendor_can_issue_license_to_direct_customer():
    vendor = SimpleNamespace(id=uuid4(), tenant_kind=edition_service.EDITION_VENDOR)
    customer = SimpleNamespace(
        id=uuid4(),
        tenant_kind=edition_service.EDITION_CUSTOMER,
        parent_tenant_id=vendor.id,
    )
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_result(vendor), _result(None), _result(None)]),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )

    row = await license_service.issue_license(
        db,
        issuer=vendor,
        tenant=customer,
        feature_codes=["workflow_runs"],
    )

    assert row.issuer_tenant_id == vendor.id
    assert row.tenant_id == customer.id
    assert row.edition == edition_service.EDITION_CUSTOMER
    assert db.execute.await_count == 3


@pytest.mark.asyncio
async def test_vendor_cannot_issue_license_to_another_vendors_customer():
    vendor = SimpleNamespace(id=uuid4(), tenant_kind=edition_service.EDITION_VENDOR)
    other_vendor = SimpleNamespace(
        id=uuid4(),
        tenant_kind=edition_service.EDITION_VENDOR,
        parent_tenant_id=None,
    )
    customer = SimpleNamespace(
        id=uuid4(),
        tenant_kind=edition_service.EDITION_CUSTOMER,
        parent_tenant_id=other_vendor.id,
    )
    db = SimpleNamespace(execute=AsyncMock(return_value=_result(other_vendor)))

    with pytest.raises(ConflictError, match="outside the vendor tenant hierarchy"):
        await license_service.issue_license(db, issuer=vendor, tenant=customer)

    assert db.execute.await_count == 1