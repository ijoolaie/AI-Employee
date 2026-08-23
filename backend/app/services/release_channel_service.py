"""Release-channel and supported-version policy for commercial editions."""
from __future__ import annotations

import re
from dataclasses import dataclass


_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


@dataclass(frozen=True)
class ReleaseChannelPolicy:
    channel: str
    minimum_supported_version: str
    supported_versions: tuple[str, ...]

    def is_supported(self, version: str) -> bool:
        return version in self.supported_versions and not is_older_than(version, self.minimum_supported_version)


def _version_tuple(version: str) -> tuple[int, int, int]:
    match = _VERSION_RE.fullmatch(version.strip())
    if match is None:
        raise ValueError(f"Invalid release version: {version}")
    return tuple(int(part) for part in match.groups())


def is_older_than(version: str, minimum_version: str) -> bool:
    return _version_tuple(version) < _version_tuple(minimum_version)


def assert_upgrade_allowed(current_version: str, target_version: str, policy: ReleaseChannelPolicy) -> None:
    if not policy.is_supported(target_version):
        raise ValueError(f"Target version {target_version} is not supported on channel {policy.channel}")
    if is_older_than(target_version, current_version):
        raise ValueError("Downgrade is not an upgrade; use the rollback workflow")


def default_policies() -> dict[str, ReleaseChannelPolicy]:
    return {
        "vendor": ReleaseChannelPolicy(
            channel="vendor",
            minimum_supported_version="v1.1.0",
            supported_versions=("v1.1.0", "v1.1.1", "v1.1.2"),
        ),
        "reseller": ReleaseChannelPolicy(
            channel="reseller",
            minimum_supported_version="v1.1.1",
            supported_versions=("v1.1.1", "v1.1.2"),
        ),
        "customer": ReleaseChannelPolicy(
            channel="customer",
            minimum_supported_version="v1.1.1",
            supported_versions=("v1.1.1", "v1.1.2"),
        ),
    }
