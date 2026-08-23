import pytest

from app.services.release_channel_service import (
    ReleaseChannelPolicy,
    assert_upgrade_allowed,
    default_policies,
    is_older_than,
)


def test_release_channels_define_supported_versions():
    policies = default_policies()
    assert set(policies) == {"vendor", "reseller", "customer"}
    assert policies["vendor"].is_supported("v1.1.2")
    assert policies["customer"].is_supported("v1.1.1")
    assert not policies["customer"].is_supported("v1.1.0")


def test_version_ordering_is_semver_like():
    assert is_older_than("v1.1.1", "v1.1.2")
    assert not is_older_than("v1.1.2", "v1.1.2")


def test_upgrade_rejects_unsupported_target():
    policy = ReleaseChannelPolicy(
        channel="customer",
        minimum_supported_version="v1.1.1",
        supported_versions=("v1.1.1", "v1.1.2"),
    )
    with pytest.raises(ValueError, match="not supported"):
        assert_upgrade_allowed("v1.1.1", "v1.1.3", policy)


def test_upgrade_rejects_downgrade():
    policy = default_policies()["customer"]
    with pytest.raises(ValueError, match="Downgrade"):
        assert_upgrade_allowed("v1.1.2", "v1.1.1", policy)
