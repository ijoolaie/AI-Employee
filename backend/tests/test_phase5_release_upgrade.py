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


def test_customer_upgrade_allows_current_certified_release():
    tenant = _tenant("customer", None)

    assert_tenant_upgrade_allowed(
        tenant=tenant,
        target_version="v1.2.0",
    )


def test_customer_upgrade_rejects_historical_target():
    tenant = _tenant("customer", "v1.2.0")

    with pytest.raises(ValueError, match="not supported"):
        assert_tenant_upgrade_allowed(
            tenant=tenant,
            target_version="v1.1.2",
        )


def test_customer_upgrade_rejects_downgrade_from_current_release():
    policy = default_policies()["customer"]
    tenant = _tenant("customer", "v1.2.0")

    with pytest.raises(ValueError, match="Downgrade"):
        from app.services.release_channel_service import assert_upgrade_allowed

        assert_upgrade_allowed(
            current_version=tenant.vendor_release_tag,
            target_version="v1.1.2",
            policy=policy,
        )


def test_unknown_edition_channel_fails_closed():
    tenant = _tenant("unknown", "v1.2.0")

    with pytest.raises(ValueError, match="Unsupported tenant edition channel"):
        assert_tenant_upgrade_allowed(
            tenant=tenant,
            target_version="v1.2.0",
        )


@pytest.mark.asyncio
async def test_upgrade_tenant_release_persists_and_audits(monkeypatch):
    tenant = _tenant("customer", None)

    db = AsyncMock()
    audit = AsyncMock()

    monkeypatch.setattr(
        "app.services.edition_service.record_audit",
        audit,
    )

    result = await upgrade_tenant_release(
        db,
        tenant=tenant,
        target_version="v1.2.0",
        actor_id="actor-1",
    )

    assert result.vendor_release_tag == "v1.2.0"
    db.flush.assert_awaited_once()

    audit.assert_awaited_once()
    kwargs = audit.await_args.kwargs

    assert kwargs["action"] == "release.upgraded"
    assert kwargs["resource_id"] == "tenant-1"
    assert kwargs["metadata"]["from_version"] is None
    assert kwargs["metadata"]["to_version"] == "v1.2.0"
    assert kwargs["metadata"]["channel"] == "customer"


@pytest.mark.asyncio
async def test_upgrade_to_same_version_is_idempotent():
    tenant = _tenant("customer", "v1.2.0")
    db = AsyncMock()

    result = await upgrade_tenant_release(
        db,
        tenant=tenant,
        target_version="v1.2.0",
    )

    assert result.vendor_release_tag == "v1.2.0"
    db.flush.assert_not_awaited()


def test_policies_remain_explicit():
    policies = default_policies()

    assert policies["vendor"].supported_versions == ("v1.2.0",)
    assert policies["reseller"].minimum_supported_version == "v1.2.0"
    assert policies["customer"].minimum_supported_version == "v1.2.0"
