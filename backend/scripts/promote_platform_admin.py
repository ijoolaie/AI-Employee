"""Explicitly promote one existing user to platform administrator.

Usage:
  python scripts/promote_platform_admin.py --tenant-slug acme --email admin@example.com

This is intentionally an explicit operator action. Tenant superusers are NOT
implicitly platform administrators.
"""
from __future__ import annotations

import argparse

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.tenant import Tenant
from app.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant-slug", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    settings = get_settings()
    engine = create_engine(settings.database_url_sync)
    with Session(engine) as db:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == args.tenant_slug))
        if tenant is None:
            raise SystemExit("Tenant not found")
        user = db.scalar(select(User).where(User.tenant_id == tenant.id, User.email == args.email.lower()))
        if user is None:
            raise SystemExit("User not found in tenant")
        if not user.is_active:
            raise SystemExit("User is inactive")
        user.is_platform_admin = True
        db.commit()
        print(f"Platform admin granted: {user.email} ({tenant.slug})")


if __name__ == "__main__":
    main()
