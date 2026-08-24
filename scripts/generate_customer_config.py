#!/usr/bin/env python3
"""Generate a secret-free customer .env template from the approved template."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "config" / "templates" / ".env.customer.example"

REQUIRED_MARKERS = ("<CUSTOMER_DOMAIN>", "<GENERATE_STRONG_SECRET>", "<URL_ENCODED_PASSWORD>")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="dist/config/.env.customer.example")
    parser.add_argument("--domain", help="Customer hostname; replaces <CUSTOMER_DOMAIN>")
    args = parser.parse_args()
    text = TEMPLATE.read_text(encoding="utf-8")
    if args.domain:
        domain = args.domain.strip().replace("https://", "").rstrip("/")
        if not domain or any(ch.isspace() for ch in domain):
            raise SystemExit("invalid --domain")
        text = text.replace("<CUSTOMER_DOMAIN>", domain)
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(f"wrote {output}")
    print("No secrets were generated or written; placeholders require operator-managed secret generation.")

if __name__ == "__main__":
    main()
