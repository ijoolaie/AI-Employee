from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.marketplace import MarketplaceError, MarketplaceService


class Result:
    def __init__(self, row=None, scalar=None, items=None):
        self._row = row
        self._scalar = scalar
        self._items = items or []

    def one_or_none(self):
        return self._row

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: self._items)


class FakeSession:
    def __init__(self, rows):
        self.rows = iter(rows)
        self.added = []

    async def execute(self, _stmt):
        return next(self.rows)

    def add(self, item):
        self.added.append(item)

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_publish_rejects_non_owner():
    owner_id = uuid4()
    version = SimpleNamespace(id=uuid4(), version=1, member_agent_definition_ids=[uuid4()])
    team = SimpleNamespace(id=uuid4(), tenant_id=owner_id, enabled=True)
    db = FakeSession([Result(row=(version, team))])

    with pytest.raises(MarketplaceError, match="owning tenant"):
        await MarketplaceService(db).publish(
            owner_tenant_id=uuid4(),
            team_version_id=version.id,
            actor_id=uuid4(),
            visibility="public",
            title="Team",
        )


@pytest.mark.asyncio
async def test_publish_creates_discovery_record_without_acceptance_semantics():
    tenant_id = uuid4()
    version = SimpleNamespace(id=uuid4(), version=1, member_agent_definition_ids=[uuid4()])
    team = SimpleNamespace(id=uuid4(), tenant_id=tenant_id, enabled=True)
    db = FakeSession([Result(row=(version, team)), Result(scalar=None)])

    publication = await MarketplaceService(db).publish(
        owner_tenant_id=tenant_id,
        team_version_id=version.id,
        actor_id=uuid4(),
        visibility="public",
        title="Public Team",
    )

    assert publication.owner_tenant_id == tenant_id
    assert publication.visibility == "public"
    assert publication.status == "published"
    assert publication.title == "Public Team"


@pytest.mark.asyncio
async def test_get_for_tenant_allows_public_but_not_private_cross_tenant():
    other_tenant = uuid4()
    public = SimpleNamespace(visibility="public", status="published")
    private = SimpleNamespace(visibility="private", status="published")

    public_db = FakeSession([Result(scalar=public)])
    assert await MarketplaceService(public_db).get_for_tenant(tenant_id=other_tenant, publication_id=uuid4()) is public

    private_db = FakeSession([Result(scalar=None)])
    with pytest.raises(MarketplaceError, match="not found"):
        await MarketplaceService(private_db).get_for_tenant(tenant_id=other_tenant, publication_id=uuid4())
