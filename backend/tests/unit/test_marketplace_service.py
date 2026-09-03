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
        for item in self.added:
            if getattr(item, "id", None) is None:
                item.id = uuid4()
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


@pytest.mark.asyncio
async def test_import_public_publication_clones_team_and_agents_into_target_tenant():
    source_tenant = uuid4()
    target_tenant = uuid4()
    source_agent_id = uuid4()
    publication_id = uuid4()
    source_version = SimpleNamespace(
        id=uuid4(),
        version=3,
        member_agent_definition_ids=[source_agent_id],
        roles={"lead": "agent"},
        execution_policy={"approval": "required"},
        allowed_tools=["calendar.read"],
        input_schema={"type": "object"},
        output_schema={"type": "object"},
    )
    source_team = SimpleNamespace(
        id=uuid4(), tenant_id=source_tenant, enabled=True,
        slug="sales-team", name="Sales Team", description="Sales automation",
    )
    publication = SimpleNamespace(
        id=publication_id, owner_tenant_id=source_tenant,
        team_version_id=source_version.id, visibility="public", status="published",
    )
    source_agent = SimpleNamespace(
        id=source_agent_id, tenant_id=source_tenant, slug="sales-agent", name="Sales Agent",
        description="Seller", version=2, capabilities=["sales"], allowed_tools=["calendar.read"],
        model_policy={"model": "safe"}, input_schema={"type": "object"},
        output_schema={"type": "object"}, policy_requirements={"approval": True}, enabled=True,
    )
    db = FakeSession([
        Result(row=(publication, source_version, source_team)),
        Result(scalar=None),
        Result(items=[source_agent]),
    ])

    installation = await MarketplaceService(db).import_publication(
        tenant_id=target_tenant,
        publication_id=publication_id,
        actor_id=uuid4(),
        workspace_key="customer-a",
    )

    imported_agent, imported_team, imported_version = db.added[:3]
    assert imported_agent.tenant_id == target_tenant
    assert imported_agent.id != source_agent_id
    assert imported_agent.slug.startswith("sales-agent-marketplace-")
    assert imported_team.tenant_id == target_tenant
    assert imported_team.id != source_team.id
    assert imported_team.slug.startswith("sales-team-marketplace-")
    assert imported_version.team_id == imported_team.id
    assert imported_version.version == source_version.version
    assert imported_version.member_agent_definition_ids == [str(imported_agent.id)]
    assert installation.tenant_id == target_tenant
    assert installation.source_publication_id == publication_id
    assert installation.team_version_id == imported_version.id


@pytest.mark.asyncio
async def test_import_rejects_duplicate_publication_scope():
    target_tenant = uuid4()
    publication_id = uuid4()
    existing = SimpleNamespace(id=uuid4())
    publication = SimpleNamespace(id=publication_id, visibility="public", status="published")
    source_version = SimpleNamespace(version=1, member_agent_definition_ids=[uuid4()])
    source_team = SimpleNamespace(enabled=True)
    db = FakeSession([
        Result(row=(publication, source_version, source_team)),
        Result(scalar=existing),
    ])

    with pytest.raises(MarketplaceError, match="already installed"):
        await MarketplaceService(db).import_publication(
            tenant_id=target_tenant,
            publication_id=publication_id,
            actor_id=uuid4(),
        )
