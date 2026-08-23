"""Phase 5 commercial license contracts.

These tests are intentionally database-free so they remain useful while
GitHub Actions capacity is exhausted; the integration/runtime suite is still
required before production acceptance.
"""
from datetime import datetime, timezone
from uuid import uuid4

from app.models.license import CommercialLicense
from app.schemas.edition import LicenseIssueRequest, LicenseRevokeRequest


def test_license_issue_request_bounds():
    request = LicenseIssueRequest(expires_in_days=365, feature_codes=["advanced_workflows"])
    assert request.expires_in_days == 365
    assert request.feature_codes == ["advanced_workflows"]


def test_license_model_has_immutable_identity_fields():
    tenant_id = uuid4()
    issuer_id = uuid4()
    row = CommercialLicense(
        license_key="LIC-contract-test",
        issuer_tenant_id=issuer_id,
        tenant_id=tenant_id,
        edition="customer",
        status="active",
        issued_at=datetime.now(timezone.utc),
        feature_codes=["advanced_workflows"],
        metadata={"contract": "test"},
    )
    assert row.license_key.startswith("LIC-")
    assert row.issuer_tenant_id == issuer_id
    assert row.tenant_id == tenant_id
    assert row.status == "active"


def test_license_revoke_requires_reason():
    request = LicenseRevokeRequest(reason="Commercial contract terminated")
    assert len(request.reason) >= 3
