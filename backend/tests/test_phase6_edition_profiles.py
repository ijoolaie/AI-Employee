import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
EXPECTED = {
    "vendor": ("vendor", "product", None),
    "reseller": ("reseller", "delegated", "vendor"),
    "customer": ("customer", "consumed", "reseller-or-vendor"),
}


def test_all_three_edition_profiles_exist_and_have_distinct_contracts():
    for edition, (channel, authority, parent) in EXPECTED.items():
        path = ROOT / "delivery" / "profiles" / edition / "profile.json"
        assert path.exists(), path
        profile = json.loads(path.read_text(encoding="utf-8"))
        assert profile["schema_version"] == 1
        assert profile["edition"] == edition
        assert profile["release_channel"] == channel
        assert profile["authority"] == authority
        assert profile["parent_edition"] == parent
        assert profile["secret_policy"] != "included"


def test_vendor_is_the_only_product_authority():
    profiles = {
        edition: json.loads(
            (ROOT / "delivery" / "profiles" / edition / "profile.json").read_text(encoding="utf-8")
        )
        for edition in EXPECTED
    }
    assert profiles["vendor"]["authority"] == "product"
    assert profiles["reseller"]["authority"] == "delegated"
    assert profiles["customer"]["authority"] == "consumed"


def test_existing_delivery_manifests_share_one_vendor_identity():
    manifests = [
        ROOT / "delivery/manifests/vendor/v1.1.0.yaml",
        ROOT / "delivery/manifests/reseller/v1.1.0-reseller.1.yaml",
        ROOT / "delivery/manifests/customer/v1.1.0-customer.1.yaml",
    ]
    texts = [path.read_text(encoding="utf-8") for path in manifests]
    assert all("vendor_release_tag: v1.1.0" in text for text in texts)
    assert all("vendor_commit_sha: ab477b84a3f9f2441d2029a732a21d534fd217b9" in text for text in texts)
    assert "reseller_delivery_id: v1.1.0-reseller.1" in texts[2]
