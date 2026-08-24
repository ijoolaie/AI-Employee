#!/usr/bin/env python3
"""Validate the three Phase 6 edition profile contracts without external dependencies."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "delivery" / "profiles"
MANIFESTS = ROOT / "delivery" / "manifests"

EXPECTED = {
    "vendor": {
        "authority": "product",
        "channel": "vendor",
        "parent": None,
    },
    "reseller": {
        "authority": "delegated",
        "channel": "reseller",
        "parent": "vendor",
    },
    "customer": {
        "authority": "consumed",
        "channel": "customer",
        "parent": "reseller-or-vendor",
    },
}


def _read_profile(edition: str) -> dict:
    path = PROFILES / edition / "profile.json"
    if not path.exists():
        raise SystemExit(f"missing profile: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*([^#\n]+?)\s*$", text)
    return match.group(1).strip() if match else None


def main() -> None:
    profiles = {edition: _read_profile(edition) for edition in EXPECTED}

    for edition, expected in EXPECTED.items():
        profile = profiles[edition]
        if profile.get("schema_version") != 1:
            raise SystemExit(f"{edition}: schema_version must be 1")
        if profile.get("edition") != edition:
            raise SystemExit(f"{edition}: profile edition mismatch")
        if profile.get("release_channel") != expected["channel"]:
            raise SystemExit(f"{edition}: release channel mismatch")
        if profile.get("authority") != expected["authority"]:
            raise SystemExit(f"{edition}: authority mismatch")
        if profile.get("parent_edition") != expected["parent"]:
            raise SystemExit(f"{edition}: parent edition mismatch")
        if profile.get("secret_policy") == "included":
            raise SystemExit(f"{edition}: secrets may not be included")

    vendor = (MANIFESTS / "vendor/v1.1.0.yaml").read_text(encoding="utf-8")
    reseller = (MANIFESTS / "reseller/v1.1.0-reseller.1.yaml").read_text(encoding="utf-8")
    customer = (MANIFESTS / "customer/v1.1.0-customer.1.yaml").read_text(encoding="utf-8")

    vendor_tag = _scalar(vendor, "vendor_release_tag")
    vendor_sha = _scalar(vendor, "vendor_commit_sha")
    if not vendor_tag or not vendor_sha:
        raise SystemExit("vendor manifest must define immutable vendor identity")

    for name, text in (("reseller", reseller), ("customer", customer)):
        if _scalar(text, "vendor_release_tag") != vendor_tag:
            raise SystemExit(f"{name}: vendor release tag diverges from vendor manifest")
        if _scalar(text, "vendor_commit_sha") != vendor_sha:
            raise SystemExit(f"{name}: vendor commit SHA diverges from vendor manifest")
        if re.search(r"(?mi)^\s*included:\s*true\s*$", text):
            raise SystemExit(f"{name}: manifest must not include secrets")

    if _scalar(customer, "reseller_delivery_id") != _scalar(reseller, "release_id"):
        raise SystemExit("customer: reseller delivery identity does not reference the reseller profile")

    print("phase6 edition profiles valid")
    print(f"vendor_release_tag={vendor_tag}")
    print(f"vendor_commit_sha={vendor_sha}")
    print("profiles=vendor,reseller,customer")


if __name__ == "__main__":
    main()
