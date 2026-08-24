from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.release_channel_service import (
    assert_tenant_upgrade_allowed,
    default_policies,
    upgrade_tenant_release,
)


def _tenant(kind: str, version: str | None):
    return SimpleNamespace(
        id="tenant-1",
        tenant_kind=kind,
        vendor_release_tag=version,
    )


def test_vendor_upgrade_allows_supported_forward_release():
    tenant = _tenant("vendor", "v1.1.1")

    assert_tenant_upgrade_allowed(
        tenant=tenant,
        target_version="v1.1.2",
    )


def test_customer_upgrade_rejects_below_channel_minimum():
    tenant = _tenant("customer", "v1.1.1")

    with pytest.raises(ValueError, match="not supported"):
        assert_tenant_upgrade_allowed(
            tenant=tenant,
            target_version="v1.1.0",
        )


def test_customer_upgrade_rejects_downgrade():
    tenant = _tenant("customer", "v1.1.2")

    with pytest.raises(ValueError, match="Downgrade"):
        assert_tenant_upgrade_allowed(
            tenant=tenant,
            target_version="v1.1.1",
        )


def test_unknown_edition_channel_fails_closed():
    tenant = _tenant("unknown", "v1.1.1")

    with pytest.raises(ValueError, match="Unsupported tenant edition channel"):
        assert_tenant_upgrade_allowed(
            tenant=tenant,
            target_version="v1.1.2",
        )


def test_initial_release_assignment_only_requires_supported_target():
    tenant = _tenant("customer", None)

    assert_tenant_upgrade_allowed(
        tenant=tenant,
        target_version="v1.1.2",
    )


@pytest.mark.asyncio
async def test_upgrade_tenant_release_persists_and_audits(monkeypatch):
    tenant = _tenant("customer", "v1.1.1")

    db = AsyncMock()
    audit = AsyncMock()

    monkeypatch.setattr(
        "app.services.edition_service.record_audit",
        audit,
    )

    result = await upgrade_tenant_release(
        db,
        tenant=tenant,
        target_version="v1.1.2",
        actor_id="actor-1",
    )

    assert result.vendor_release_tag == "v1.1.2"
    db.flush.assert_awaited_once()

    audit.assert_awaited_once()
    kwargs = audit.await_args.kwargs

    assert kwargs["action"] == "release.upgraded"
    assert kwargs["resource_id"] == "tenant-1"
    assert kwargs["metadata"]["from_version"] == "v1.1.1"
    assert kwargs["metadata"]["to_version"] == "v1.1.2"
    assert kwargs["metadata"]["channel"] == "customer"


@pytest.mark.asyncio
async def test_upgrade_to_same_version_is_idempotent():
    tenant = _tenant("customer", "v1.1.2")
    db = AsyncMock()
    audit = AsyncMock()

    result = await upgrade_tenant_release(
        db,
        tenant=tenant,
        target_version="v1.1.2",
    )

    assert result.vendor_release_tag == "v1.1.2"
    db.flush.assert_not_awaited()


def test_policies_remain_explicit():
    policies = default_policies()

    assert policies["vendor"].supported_versions == (
        "v1.1.0",
        "v1.1.1",
        "v1.1.2",
    )
    assert policies["reseller"].minimum_supported_version == "v1.1.1"
    assert policies["customer"].minimum_supported_version == "v1.1.1"
