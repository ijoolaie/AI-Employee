from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ConflictError
from app.schemas.edition import LicenseIssueRequest
from app.services import edition_service, license_service


class _Result:
    def __init__(self, value=None):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _IssueDB:
    def __init__(self, results):
        self.results = iter(results)
        self.added = []

    async def execute(self, _statement):
        return next(self.results)

    def add(self, row):
        self.added.append(row)

    async def flush(self):
        return None

    async def refresh(self, _row):
        return None


@pytest.mark.asyncio
async def test_vendor_can_issue_license_to_customer_under_its_reseller(monkeypatch):
    vendor_id = "vendor-id"
    reseller = SimpleNamespace(id="reseller-id", parent_tenant_id=vendor_id)
    customer = SimpleNamespace(
        id="customer-id",
        parent_tenant_id=reseller.id,
        tenant_kind=edition_service.EDITION_CUSTOMER,
    )
    issuer = SimpleNamespace(id=vendor_id, tenant_kind=edition_service.EDITION_VENDOR)
    db = _IssueDB([_Result(reseller), _Result(), _Result(None)])
    monkeypatch.setattr(edition_service, "record_audit", AsyncMock())

    license_row = await license_service.issue_license(
        db,
        issuer=issuer,
        tenant=customer,
        feature_codes=["run.execute"],
    )

    assert license_row.tenant_id == customer.id
    assert license_row.issuer_tenant_id == vendor_id
    assert license_row.edition == edition_service.EDITION_CUSTOMER
    assert license_row.feature_codes == ["run.execute"]


@pytest.mark.asyncio
async def test_vendor_cannot_issue_license_outside_its_hierarchy():
    vendor = SimpleNamespace(id="vendor-id", tenant_kind=edition_service.EDITION_VENDOR)
    other_vendor = SimpleNamespace(id="other-vendor", parent_tenant_id=None)
    other_reseller = SimpleNamespace(
        id="other-reseller",
        parent_tenant_id=other_vendor.id,
    )
    customer = SimpleNamespace(
        id="foreign-customer",
        parent_tenant_id=other_reseller.id,
        tenant_kind=edition_service.EDITION_CUSTOMER,
    )
    db = _IssueDB([_Result(other_reseller), _Result(other_vendor)])

    with pytest.raises(ConflictError, match="outside the vendor tenant hierarchy"):
        await license_service.issue_license(
            db,
            issuer=vendor,
            tenant=customer,
            feature_codes=["run.execute"],
        )

@pytest.mark.parametrize("feature_codes", [[""], ["   "], ["run.execute", " \t "]])
def test_license_issue_request_rejects_blank_feature_codes(feature_codes):
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="feature codes must not be blank"):
        LicenseIssueRequest(feature_codes=feature_codes)


def test_license_issue_request_strips_feature_code_whitespace():
    request = LicenseIssueRequest(feature_codes=["  run.execute  "])

    assert request.feature_codes == ["run.execute"]

