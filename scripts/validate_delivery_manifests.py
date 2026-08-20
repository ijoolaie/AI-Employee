from pathlib import Path
import re
import subprocess

VENDOR_TAG = "v1.1.0"
VENDOR_SHA = "ab477b84a3f9f2441d2029a732a21d534fd217b9"
ROOT = Path("delivery/manifests")

EXPECTED = {
    "vendor/v1.1.0.yaml": {
        "edition": "vendor",
        "release_id": "v1.1.0",
    },
    "reseller/v1.1.0-reseller.1.yaml": {
        "edition": "reseller",
        "release_id": "v1.1.0-reseller.1",
    },
    "customer/v1.1.0-customer.1.yaml": {
        "edition": "end-customer",
        "release_id": "v1.1.0-customer.1",
    },
}


def scalar(text: str, key: str) -> str | None:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*([^#\n]+?)\s*$", text)
    return match.group(1).strip() if match else None


def require(text: str, key: str, value: str, path: Path) -> None:
    actual = scalar(text, key)
    if actual != value:
        raise SystemExit(f"{path}: {key} must be {value!r}, got {actual!r}")


def main() -> None:
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        if not path.exists():
            raise SystemExit(f"missing manifest: {path}")
        text = path.read_text(encoding="utf-8")

        require(text, "schema_version", "1", path)
        require(text, "edition", expected["edition"], path)
        require(text, "release_id", expected["release_id"], path)
        require(text, "vendor_release_tag", VENDOR_TAG, path)
        require(text, "vendor_commit_sha", VENDOR_SHA, path)

        if re.search(r"(?mi)^\s*included:\s*true\s*$", text):
            raise SystemExit(f"{path}: secrets.included must never be true")
        if "RESELLER-EXAMPLE-001" not in text and expected["edition"] == "reseller":
            raise SystemExit(f"{path}: expected reseller identity placeholder")
        if "CUSTOMER-EXAMPLE-001" not in text and expected["edition"] == "end-customer":
            raise SystemExit(f"{path}: expected customer identity placeholder")

    customer = (ROOT / "customer/v1.1.0-customer.1.yaml").read_text(encoding="utf-8")
    require(customer, "reseller_delivery_id", "v1.1.0-reseller.1", ROOT / "customer/v1.1.0-customer.1.yaml")

    tag_sha = subprocess.check_output(
        ["git", "rev-list", "-n", "1", VENDOR_TAG], text=True
    ).strip()
    if tag_sha != VENDOR_SHA:
        raise SystemExit(
            f"vendor tag {VENDOR_TAG} resolves to {tag_sha}, expected {VENDOR_SHA}"
        )

    print("delivery manifests valid and vendor release identity is immutable")


if __name__ == "__main__":
    main()
