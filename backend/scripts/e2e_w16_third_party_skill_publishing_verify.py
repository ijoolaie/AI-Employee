"""Real-stack W16 third-party SkillPackage publishing and discovery verification."""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.skill_marketplace_publication import SkillMarketplacePublication
from app.models.tenant import Tenant
from app.services import edition_lifecycle_service, skill_marketplace_service
from app.services.skill_marketplace_publication_service import SkillMarketplacePublicationService

BASE_URL = os.environ.get("E2E_API_BASE_URL", "http://localhost:8000/api/v1")


def request(method: str, path: str, payload: dict | None = None, token: str | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=10) as response:
            raw = response.read().decode()
            return response.status, json.loads(raw) if raw else {}
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"raw": raw}
    except URLError as exc:
        raise AssertionError(f"{method} {path} unavailable: {exc}") from exc


def assert_status(actual: int, expected: int, label: str, body: dict) -> None:
    assert actual == expected, f"{label}: expected HTTP {expected}, got {actual}: {body}"


def register(suffix: str, label: str) -> tuple[str, str]:
    tenant_slug = f"w16-skill-pub-{label}-{suffix}"
    status, response = request(
        "POST",
        "/auth/register",
        {
            "tenant_name": f"W16 Skill Publication {label} Tenant {suffix}",
            "tenant_slug": tenant_slug,
            "email": f"w16-skill-pub-{label}-{suffix}@example.com",
            "password": "W16SkillPublishE2E-2026!",
            "full_name": f"W16 Skill Publication {label} Admin",
        },
    )
    assert_status(status, 201, f"{label} registration", response)
    token = (response.get("data") or {}).get("access_token")
    assert token, f"{label} registration did not return an access token"
    return tenant_slug, token


async def create_published_package(tenant_slug: str, slug: str, actor_id: str) -> tuple[str, str]:
    async with AsyncSessionLocal() as db:
        tenant = (await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))).scalar_one()
        package = await skill_marketplace_service.create_package(
            db,
            tenant_id=tenant.id,
            slug=slug,
            name="Third-party Published Skill",
            version=1,
            description="Public marketplace publication fixture",
            manifest={"entrypoint": "presentation-only"},
            compatibility={"employee_kinds": ["custom"]},
            presentation_metadata={"icon": "skill"},
        )
        await skill_marketplace_service.publish_package(
            db,
            tenant_id=tenant.id,
            package_id=package.id,
            actor_id=uuid.UUID(actor_id),
        )
        await db.commit()
        return str(tenant.id), str(package.id)


async def create_publication(
    tenant_slug: str,
    package_id: str,
    actor_id: str,
    *,
    visibility: str,
    title: str,
) -> str:
    async with AsyncSessionLocal() as db:
        tenant = (await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))).scalar_one()
        publication = await SkillMarketplacePublicationService.publish(
            db,
            owner_tenant_id=tenant.id,
            skill_package_id=uuid.UUID(package_id),
            actor_id=uuid.UUID(actor_id),
            visibility=visibility,
            title=title,
        )
        await db.commit()
        return str(publication.id)


async def cleanup(slugs: list[str]) -> None:
    if not slugs:
        return
    async with AsyncSessionLocal() as db:
        tenants = list((await db.execute(select(Tenant).where(Tenant.slug.in_(slugs)))).scalars().all())
        for tenant in tenants:
            if tenant.status != edition_lifecycle_service.STATUS_DEPROVISIONED:
                await edition_lifecycle_service.transition_tenant_status(
                    db,
                    tenant=tenant,
                    target_status=edition_lifecycle_service.STATUS_DEPROVISIONED,
                    actor_id=None,
                    audit_tenant_id=tenant.id,
                    audit_metadata={"certification_fixture": True, "cleanup_mode": "deprovision"},
                )
        await db.commit()


async def verify_publication_immutability(publication_id: str, original_title: str) -> None:
    async with AsyncSessionLocal() as db:
        publication = (
            await db.execute(
                select(SkillMarketplacePublication).where(
                    SkillMarketplacePublication.id == uuid.UUID(publication_id)
                )
            )
        ).scalar_one()
        publication.title = "forbidden mutation"
        try:
            await db.flush()
        except ValueError:
            await db.rollback()
        else:
            raise AssertionError("publication mutation was not rejected")

        persisted = (
            await db.execute(
                select(SkillMarketplacePublication.title).where(
                    SkillMarketplacePublication.id == uuid.UUID(publication_id)
                )
            )
        ).scalar_one()
        assert persisted == original_title, "publication mutation changed persisted metadata"


def main() -> int:
    suffix = str(time.time_ns())[-12:]
    slugs: list[str] = []
    try:
        tenant_a, token_a = register(suffix, "a")
        tenant_b, token_b = register(suffix, "b")
        slugs.extend([tenant_a, tenant_b])

        status, me_a = request("GET", "/auth/me", token=token_a)
        assert_status(status, 200, "tenant A current-user", me_a)
        actor_a = (me_a.get("data") or {}).get("user", {}).get("id")
        assert actor_a

        tenant_a_id, package_a = asyncio.run(
            create_published_package(tenant_a, f"third-party-skill-{suffix}", actor_a)
        )

        status, own_publish = request(
            "POST",
            "/skill-marketplace/publications",
            {
                "skill_package_id": package_a,
                "visibility": "public",
                "title": "Third-party Public Skill",
                "summary": "Public discovery fixture",
            },
            token=token_a,
        )
        assert_status(status, 201, "owner publishes public skill", own_publish)
        publication_id = (own_publish.get("data") or {}).get("id")
        assert publication_id
        assert (own_publish.get("data") or {}).get("installation") == "not_implied"
        assert (own_publish.get("data") or {}).get("execution_authority") == "not_implied"
        print("THIRD-PARTY SKILL PUBLICATION PASS")

        status, cross_list = request(
            "GET",
            "/skill-marketplace/publications",
            token=token_b,
        )
        assert_status(status, 200, "cross-tenant public discovery", cross_list)
        public_ids = {(item or {}).get("id") for item in (cross_list.get("data") or [])}
        assert publication_id in public_ids
        print("CROSS-TENANT PUBLIC DISCOVERY PASS")

        status, cross_get = request(
            "GET",
            f"/skill-marketplace/publications/{publication_id}",
            token=token_b,
        )
        assert_status(status, 200, "cross-tenant public lookup", cross_get)
        cross_data = cross_get.get("data") or {}
        assert cross_data.get("owner_tenant_id") == tenant_a_id
        assert "manifest" not in cross_data
        assert "compatibility" not in cross_data
        print("CROSS-TENANT PUBLIC LOOKUP + METADATA BOUNDARY PASS")

        private_package = asyncio.run(
            create_published_package(tenant_a, f"private-skill-{suffix}", actor_a)
        )
        private_publication = asyncio.run(
            create_publication(
                tenant_a,
                private_package[1],
                actor_a,
                visibility="private",
                title="Private Skill Listing",
            )
        )

        status, private_get = request(
            "GET",
            f"/skill-marketplace/publications/{private_publication}",
            token=token_b,
        )
        assert_status(status, 404, "cross-tenant private publication hidden", private_get)
        print("CROSS-TENANT PRIVATE PUBLICATION HIDDEN PASS")

        status, wrong_owner_publish = request(
            "POST",
            "/skill-marketplace/publications",
            {
                "skill_package_id": package_a,
                "visibility": "public",
                "title": "Wrong Owner Attempt",
            },
            token=token_b,
        )
        assert_status(status, 404, "wrong-tenant publication rejected", wrong_owner_publish)
        print("WRONG-TENANT PUBLICATION REJECT PASS")

        status, duplicate = request(
            "POST",
            "/skill-marketplace/publications",
            {
                "skill_package_id": package_a,
                "visibility": "public",
                "title": "Duplicate Attempt",
            },
            token=token_a,
        )
        assert_status(status, 409, "duplicate publication rejected", duplicate)
        print("DUPLICATE PUBLICATION REJECT PASS")

        asyncio.run(verify_publication_immutability(publication_id, "Third-party Public Skill"))
        print("PUBLICATION IMMUTABILITY PASS")

        print("W16 THIRD-PARTY SKILL PUBLISHING + DISCOVERY REAL-STACK PASS")
        return 0
    finally:
        try:
            asyncio.run(cleanup(slugs))
        except Exception as exc:
            print(f"CERTIFICATION FIXTURE CLEANUP FAIL: {type(exc).__name__}", file=sys.stderr)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"W16 THIRD-PARTY SKILL PUBLISHING REAL-STACK GATE FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
