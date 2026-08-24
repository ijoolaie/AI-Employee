from dataclasses import dataclass
import re


_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")

CURRENT_RELEASE_VERSION = "v1.2.0"


@dataclass(frozen=True)
class ReleaseChannelPolicy:
    channel: str
    minimum_supported_version: str
    supported_versions: tuple[str, ...]

    def is_supported(self, version: str) -> bool:
        return (
            version in self.supported_versions
            and not is_older_than(version, self.minimum_supported_version)
        )


def _version_tuple(version: str) -> tuple[int, int, int]:
    match = _VERSION_RE.fullmatch(version.strip())
    if match is None:
        raise ValueError(f"Invalid release version: {version}")
    return tuple(int(part) for part in match.groups())


def is_older_than(version: str, minimum_version: str) -> bool:
    return _version_tuple(version) < _version_tuple(minimum_version)


def assert_upgrade_allowed(
    current_version: str,
    target_version: str,
    policy: ReleaseChannelPolicy,
) -> None:
    if not policy.is_supported(target_version):
        raise ValueError(
            f"Target version {target_version} is not supported on channel {policy.channel}"
        )
    if is_older_than(target_version, current_version):
        raise ValueError("Downgrade is not an upgrade; use the rollback workflow")


def default_policies() -> dict[str, ReleaseChannelPolicy]:
    return {
        "vendor": ReleaseChannelPolicy(
            channel="vendor",
            minimum_supported_version=CURRENT_RELEASE_VERSION,
            supported_versions=(CURRENT_RELEASE_VERSION,),
        ),
        "reseller": ReleaseChannelPolicy(
            channel="reseller",
            minimum_supported_version=CURRENT_RELEASE_VERSION,
            supported_versions=(CURRENT_RELEASE_VERSION,),
        ),
        "customer": ReleaseChannelPolicy(
            channel="customer",
            minimum_supported_version=CURRENT_RELEASE_VERSION,
            supported_versions=(CURRENT_RELEASE_VERSION,),
        ),
    }


def assert_tenant_upgrade_allowed(
    *,
    tenant,
    target_version: str,
    policies: dict[str, ReleaseChannelPolicy] | None = None,
) -> None:
    """Validate a tenant release transition against its edition channel.

    v1.2.0 is the only certified release currently admitted to all commercial
    channels. Older releases remain valid historical/rollback references but
    are not accepted as new commercial delivery targets.
    """
    policies = policies or default_policies()
    channel = tenant.tenant_kind
    try:
        policy = policies[channel]
    except KeyError as exc:
        raise ValueError(f"Unsupported tenant edition channel: {channel}") from exc

    if not policy.is_supported(target_version):
        raise ValueError(
            f"Target version {target_version} is not supported on channel {channel}"
        )

    current_version = tenant.vendor_release_tag
    if current_version is None:
        return

    assert_upgrade_allowed(
        current_version=current_version,
        target_version=target_version,
        policy=policy,
    )


async def upgrade_tenant_release(
    db,
    *,
    tenant,
    target_version: str,
    actor_id=None,
    policies: dict[str, ReleaseChannelPolicy] | None = None,
):
    assert_tenant_upgrade_allowed(
        tenant=tenant,
        target_version=target_version,
        policies=policies,
    )
    current_version = tenant.vendor_release_tag
    if current_version == target_version:
        return tenant
    tenant.vendor_release_tag = target_version
    from app.services import edition_service
    await db.flush()
    await edition_service.record_audit(
        db,
        tenant_id=tenant.id,
        actor_id=actor_id,
        action="release.upgraded",
        resource_type="tenant",
        resource_id=str(tenant.id),
        metadata={
            "from_version": current_version,
            "to_version": target_version,
            "channel": tenant.tenant_kind,
        },
    )
    return tenant
