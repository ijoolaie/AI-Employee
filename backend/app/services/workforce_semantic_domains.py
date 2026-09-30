"""Governed semantic domains for workforce phases W2-W6.

This module deliberately separates internal artifact manipulation from external
side effects. All persistent artifacts are tenant-namespaced through the existing
storage abstraction. Git hosting, deployment, social publishing, commercial
outreach, and paid creative providers are represented as approval-gated proposals
until a provider adapter is configured.
"""
from __future__ import annotations

import io
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import ValidationAppError
from app.services.storage import build_key, get_storage_backend


def _tenant(arguments: dict[str, Any], context: dict[str, Any]) -> str:
    tenant_id = context.get("tenant_id")
    if not tenant_id:
        raise ValidationAppError("Workforce semantic tool requires an active tenant Run context")
    return str(tenant_id)


def _save_json(tenant_id: str, filename: str, payload: dict[str, Any]) -> dict[str, Any]:
    backend = get_storage_backend()
    key = build_key(tenant_id, filename)
    raw = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    backend.save(key, io.BytesIO(raw))
    return {"storage_key": key, "bytes": len(raw), "content_type": "application/json"}


def _read_json(tenant_id: str, storage_key: str) -> dict[str, Any]:
    if not storage_key.startswith(f"{tenant_id}/"):
        raise ValidationAppError("Cross-tenant workspace artifact access is forbidden")
    backend = get_storage_backend()
    if not backend.exists(storage_key):
        raise ValidationAppError("Workspace artifact not found")
    with backend.open(storage_key) as stream:
        return json.loads(stream.read().decode("utf-8"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def execute_engineering(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    if operation == "workspace_read":
        return _read_json(tenant_id, arguments["storage_key"])
    if operation == "workspace_list":
        prefix = f"{tenant_id}/"
        return {"tenant_id": tenant_id, "storage_keys": get_storage_backend().list_prefix(prefix)}
    if operation == "workspace_create_file":
        path = arguments["path"].strip()
        if not path or path.startswith("/") or ".." in path.split("/"):
            raise ValidationAppError("Workspace path is invalid")
        payload = {"kind": "workspace_file", "path": path, "content": arguments.get("content", ""), "created_at": _now()}
        return {**_save_json(tenant_id, f"workspace-{path.replace('/', '_')}.json", payload), "path": path}
    if operation == "workspace_edit_file":
        payload = _read_json(tenant_id, arguments["storage_key"])
        payload["content"] = arguments["content"]
        payload["updated_at"] = _now()
        backend = get_storage_backend()
        raw = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        backend.save(arguments["storage_key"], io.BytesIO(raw))
        return {"storage_key": arguments["storage_key"], "updated": True}
    if operation == "workspace_delete_file":
        if not arguments["storage_key"].startswith(f"{tenant_id}/"):
            raise ValidationAppError("Cross-tenant workspace artifact deletion is forbidden")
        backend = get_storage_backend()
        backend.delete(arguments["storage_key"])
        return {"storage_key": arguments["storage_key"], "deleted": True}
    if operation == "workspace_change_set":
        payload = {"kind": "change_set", "title": arguments["title"], "changes": arguments["changes"], "created_at": _now()}
        return {**_save_json(tenant_id, "change-set.json", payload), "status": "proposed"}
    if operation in {"workspace_test", "workspace_lint", "workspace_build"}:
        return {"operation": operation, "status": "staged", "executed": False, "reason": "Execution provider is not configured in this environment"}
    if operation in {"git_branch", "git_commit_proposal", "git_pr_proposal", "ci_status", "deploy_proposal", "health_check", "rollback_proposal"}:
        return {"operation": operation, "status": "proposal", "requires_provider": True, "approval_required": operation in {"git_commit_proposal", "git_pr_proposal", "deploy_proposal", "rollback_proposal"}}
    raise ValidationAppError("Unsupported engineering operation")


async def execute_content(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    payload = {"kind": operation, "title": arguments.get("title"), "body": arguments.get("body"), "metadata": arguments.get("metadata", {}), "created_at": _now()}
    return {**_save_json(tenant_id, f"{operation}.json", payload), "status": "draft", "approval_required": False}


async def execute_creative(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    payload = {"kind": "creative_asset_request", "operation": operation, "prompt": arguments["prompt"], "brand_context": arguments.get("brand_context"), "provider": arguments.get("provider", "local"), "created_at": _now()}
    return {**_save_json(tenant_id, f"{operation}.json", payload), "status": "draft", "provider_execution": "not_configured"}


async def execute_social(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    _tenant(arguments, context)
    operation = arguments["_operation"]
    external = operation in {"publish_post", "publish_reel", "publish_story", "schedule_publication", "respond_to_dm"}
    return {
        "operation": operation,
        "status": "proposal" if external else "ready",
        "provider": arguments.get("provider", "instagram"),
        "approval_required": external,
        "external_side_effect": external,
    }


async def execute_sales(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    _tenant(arguments, context)
    operation = arguments["_operation"]
    if operation == "lead_research":
        return {"operation": operation, "status": "research_request", "query": arguments["query"], "external_outreach": False}
    if operation == "lead_qualification":
        return {"operation": operation, "status": "qualification", "criteria": arguments.get("criteria", {})}
    return {"operation": operation, "status": "proposal", "approval_required": True, "external_side_effect": True}


async def execute_website(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    payload = {"kind": "website_change", "operation": operation, "site": arguments["site"], "spec": arguments.get("spec", {}), "created_at": _now()}
    artifact = _save_json(tenant_id, f"website-{operation}.json", payload)
    return {**artifact, "operation": operation, "status": "proposal" if operation in {"deploy", "rollback"} else "staged", "approval_required": operation in {"deploy", "rollback"}}
