from __future__ import annotations

import io
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.api.v1 import runs as runs_api


TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")
RUN_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
RUN_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


class MemoryStorage:
    def __init__(self, objects=None):
        self.objects = dict(objects or {})

    def exists(self, key):
        return key in self.objects

    def open(self, key):
        return io.BytesIO(self.objects[key])


class FakeRows:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class FakeDB:
    def __init__(self, audit_rows):
        self.audit_rows = audit_rows

    async def execute(self, statement):
        params = statement.compile().params
        tenant_id = next((value for key, value in params.items() if key.startswith("tenant_id")), None)
        action = next((value for key, value in params.items() if key.startswith("action")), None)
        resource_type = next((value for key, value in params.items() if key.startswith("resource_type")), None)
        resource_id = next((value for key, value in params.items() if key.startswith("resource_id")), None)
        rows = [
            row for row in self.audit_rows
            if row.tenant_id == tenant_id
            and row.action == action
            and row.resource_type == resource_type
            and row.resource_id == resource_id
        ]
        return FakeRows(rows)


def audit_row(*, tenant_id, run_id, artifact_id, storage_key, tool="workforce_keyword_research"):
    return SimpleNamespace(
        tenant_id=tenant_id,
        action="tool.call",
        resource_type="run",
        resource_id=str(run_id),
        created_at=datetime(2026, 10, 20, tzinfo=timezone.utc),
        metadata_={
            "persisted_workforce_artifact": {
                "artifact_id": artifact_id,
                "storage_key": storage_key,
                "tool": tool,
            }
        },
    )


def artifact_bytes(artifact_id="artifact-1"):
    return json.dumps({
        "kind": "seo_growth_artifact",
        "artifact_id": artifact_id,
        "operation": "keyword_research",
        "status": "research",
        "created_at": "2026-10-20T00:00:00+00:00",
        "provider_execution": "not_configured",
        "external_side_effect": False,
    }).encode("utf-8")


@pytest.mark.asyncio
async def test_run_artifact_is_listed_for_its_run_and_can_be_downloaded(monkeypatch):
    key = f"{TENANT_A}/seo-growth-artifact.json"
    backend = MemoryStorage({key: artifact_bytes()})
    monkeypatch.setattr(runs_api.storage, "get_storage_backend", lambda: backend)

    async def owned_run(db, *, run_id, tenant_id):
        assert run_id == RUN_A
        assert tenant_id == TENANT_A
        return SimpleNamespace(id=run_id, tenant_id=tenant_id)

    monkeypatch.setattr(runs_api.run_read_service, "get_run", owned_run)
    db = FakeDB([audit_row(tenant_id=TENANT_A, run_id=RUN_A, artifact_id="artifact-1", storage_key=key)])
    ctx = SimpleNamespace(tenant_id=TENANT_A)

    response = await runs_api.list_run_artifacts(RUN_A, ctx, db)
    assert len(response.data) == 1
    item = response.data[0]
    assert item.artifact_id == "artifact-1"
    assert item.kind == "seo_growth_artifact"
    assert item.provenance["provider_execution"] == "not_configured"
    assert "storage_key" not in item.model_dump()

    download = await runs_api.download_run_artifact(RUN_A, "artifact-1", ctx, db)
    assert download.media_type == "application/json"
    assert download.headers["content-disposition"].endswith('workforce-artifact-artifact-1.json"')


@pytest.mark.asyncio
async def test_missing_storage_object_is_not_listed(monkeypatch):
    key = f"{TENANT_A}/missing.json"
    monkeypatch.setattr(runs_api.storage, "get_storage_backend", lambda: MemoryStorage())

    async def owned_run(db, *, run_id, tenant_id):
        return SimpleNamespace(id=run_id, tenant_id=tenant_id)

    monkeypatch.setattr(runs_api.run_read_service, "get_run", owned_run)
    db = FakeDB([audit_row(tenant_id=TENANT_A, run_id=RUN_A, artifact_id="missing", storage_key=key)])
    response = await runs_api.list_run_artifacts(RUN_A, SimpleNamespace(tenant_id=TENANT_A), db)
    assert response.data == []


@pytest.mark.asyncio
async def test_artifact_from_another_run_is_not_visible(monkeypatch):
    key = f"{TENANT_A}/other-run.json"
    monkeypatch.setattr(runs_api.storage, "get_storage_backend", lambda: MemoryStorage({key: artifact_bytes()}))

    async def owned_run(db, *, run_id, tenant_id):
        return SimpleNamespace(id=run_id, tenant_id=tenant_id)

    monkeypatch.setattr(runs_api.run_read_service, "get_run", owned_run)
    db = FakeDB([audit_row(tenant_id=TENANT_A, run_id=RUN_B, artifact_id="artifact-1", storage_key=key)])
    response = await runs_api.list_run_artifacts(RUN_A, SimpleNamespace(tenant_id=TENANT_A), db)
    assert response.data == []


@pytest.mark.asyncio
async def test_cross_tenant_audit_pointer_and_storage_key_fail_closed(monkeypatch):
    tenant_b_key = f"{TENANT_B}/private.json"
    tenant_a_key = f"{TENANT_A}/mispointed.json"
    monkeypatch.setattr(
        runs_api.storage,
        "get_storage_backend",
        lambda: MemoryStorage({tenant_b_key: artifact_bytes(), tenant_a_key: artifact_bytes()}),
    )

    async def owned_run(db, *, run_id, tenant_id):
        assert tenant_id == TENANT_A
        return SimpleNamespace(id=run_id, tenant_id=tenant_id)

    monkeypatch.setattr(runs_api.run_read_service, "get_run", owned_run)
    db = FakeDB([
        audit_row(tenant_id=TENANT_B, run_id=RUN_A, artifact_id="cross-tenant", storage_key=tenant_b_key),
        audit_row(tenant_id=TENANT_A, run_id=RUN_A, artifact_id="bad-pointer", storage_key=tenant_b_key),
        audit_row(tenant_id=TENANT_A, run_id=RUN_A, artifact_id="wrong-tenant-payload", storage_key=tenant_a_key),
    ])
    response = await runs_api.list_run_artifacts(RUN_A, SimpleNamespace(tenant_id=TENANT_A), db)
    assert response.data == []
