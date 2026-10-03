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
from app.services.ai_workforce_roles import get_workforce_capability_contract
from app.services.storage import build_key, get_storage_backend
from app.services.workforce_engineering_providers import get_configured_engineering_provider, provider_contract_snapshot


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


def _approval_required(role_code: str, operation: str) -> bool:
    """Read approval state from the authoritative workforce role contract."""
    return get_workforce_capability_contract(role_code, operation).approval_required


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
        change_set_id = str(uuid.uuid4())
        payload = {
            "kind": "change_set",
            "id": change_set_id,
            "title": arguments["title"],
            "changes": arguments["changes"],
            "created_at": _now(),
        }
        return {
            **_save_json(tenant_id, f"change-set-{change_set_id}.json", payload),
            "status": "proposed",
            "change_set_id": change_set_id,
        }
    if operation in {"workspace_test", "workspace_lint", "workspace_build"}:
        provider = get_configured_engineering_provider()
        result = provider.execute(operation, tenant_id=tenant_id, arguments=arguments)
        return {
            "operation": operation,
            "status": "staged" if result.status == "not_configured" else result.status,
            "executed": result.executed,
            "provider_required": True,
            "requires_provider": True,
            "provider_execution": result.status,
            "provider": provider_contract_snapshot(provider),
            "reason": result.reason,
        }
    if operation in {"git_branch", "git_commit_proposal", "git_pr_proposal", "ci_status", "deploy_proposal", "health_check", "rollback_proposal"}:
        approval_required = _approval_required("ai_software_developer", operation)
        provider = get_configured_engineering_provider()
        result = provider.execute(operation, tenant_id=tenant_id, arguments=arguments)
        return {
            "operation": operation,
            "status": result.status if operation in {"git_branch", "ci_status"} else "proposal",
            "executed": result.executed,
            "requires_provider": True,
            "provider_required": True,
            "provider_execution": result.status,
            "provider": provider_contract_snapshot(provider),
            "provider_reason": result.reason,
            "approval_required": approval_required,
            "external_side_effect": operation in {"git_branch", "git_commit_proposal", "deploy_proposal", "rollback_proposal"},
        }
    raise ValidationAppError("Unsupported engineering operation")


async def execute_content(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    """Create a durable, versioned content artifact without overwriting prior work."""
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    content_id = str(uuid.uuid4())
    approval_required = _approval_required("ai_content_producer", operation)
    payload = {
        "kind": "content_artifact",
        "operation": operation,
        "content_id": content_id,
        "version": 1,
        "status": "draft",
        "approval_required": approval_required,
        "approval_status": "pending" if approval_required else "not_required",
        "title": arguments.get("title"),
        "body": arguments.get("body"),
        "metadata": arguments.get("metadata", {}),
        "provenance": {
            "tenant_id": tenant_id,
            "created_at": _now(),
            "provider_execution": "not_required",
        },
    }
    artifact = _save_json(tenant_id, f"content-{content_id}.json", payload)
    return {
        **artifact,
        "content_id": content_id,
        "version": 1,
        "status": "draft",
        "approval_required": approval_required,
        "approval_status": "pending" if approval_required else "not_required",
        "provider_execution": "not_required",
    }


async def execute_creative(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    """Record a governed creative request; never fake image/video provider execution."""
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    asset_id = str(uuid.uuid4())
    approval_required = _approval_required("ai_graphic_designer", operation)
    payload = {
        "kind": "creative_asset_request",
        "operation": operation,
        "asset_id": asset_id,
        "version": 1,
        "status": "draft",
        "approval_required": approval_required,
        "approval_status": "pending" if approval_required else "not_required",
        "prompt": arguments["prompt"],
        "brand_context": arguments.get("brand_context"),
        "provider_requested": arguments.get("provider"),
        "provider_execution": "not_configured",
        "provenance": {"tenant_id": tenant_id, "created_at": _now()},
    }
    artifact = _save_json(tenant_id, f"creative-{asset_id}.json", payload)
    return {
        **artifact,
        "asset_id": asset_id,
        "version": 1,
        "status": "draft",
        "approval_required": approval_required,
        "approval_status": "pending" if approval_required else "not_required",
        "provider_execution": "not_configured",
    }


async def execute_social(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    """Create a tenant-scoped social operation record without faking provider execution.

    Read/analysis operations remain non-external requests. Publication, channel
    connection, scheduling, and DM responses are durable proposals and never
    execute against Instagram until a tenant-owned provider is configured and
    the governed approval path authorizes the action.
    """
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    approval_required = _approval_required("ai_social_media", operation)
    external = operation in {
        "connect_channel", "publish_post", "publish_reel", "publish_story",
        "schedule_publication", "respond_to_dm",
    }
    social_id = str(uuid.uuid4())
    provider = arguments.get("provider", "instagram")
    provider_execution = "not_configured"
    status = "proposal" if external else "request"
    approval_status = "pending" if approval_required else "not_required"
    payload = {
        "kind": "social_operation",
        "social_id": social_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "channel": arguments.get("channel", "instagram"),
        "content_id": arguments.get("content_id"),
        "message": arguments.get("message"),
        "provider_requested": provider,
        "provider_execution": provider_execution,
        "external_side_effect": external,
        "provenance": {
            "tenant_id": tenant_id,
            "created_at": _now(),
            "provider_execution": provider_execution,
        },
    }
    artifact = _save_json(tenant_id, f"social-{social_id}.json", payload)
    return {
        **artifact,
        "social_id": social_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "provider": provider,
        "provider_execution": provider_execution,
        "external_side_effect": external,
    }

async def execute_sales(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    """Create tenant-scoped sales artifacts and execute only approved commercial commitments."""
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    approval_required = _approval_required("ai_sales_lead_generation", operation)
    external = operation in {"external_outreach", "contractual_commitment", "material_commercial_action"}
    sales_id = str(uuid.uuid4())
    provider_execution = "not_configured"
    execution_result: dict[str, Any] | None = None

    if operation == "material_commercial_action":
        db = context.get("db")
        if db is None:
            raise ValidationAppError("material_commercial_action requires an active tenant Run database context")
        from app.modules.employees.sales.service import get_deal
        deal = await get_deal(
            db,
            tenant_id=uuid.UUID(tenant_id),
            deal_id=arguments["deal_id"],
            for_update=True,
        )
        if deal.stage not in {"proposal", "negotiation"}:
            raise ValidationAppError(
                "material_commercial_action requires a deal in proposal or negotiation stage"
            )
        if deal.amount <= 0:
            raise ValidationAppError("material_commercial_action requires a positive deal amount")
        from app.services.workforce_sales_payment_provider import create_sales_checkout_session
        result = await create_sales_checkout_session(
            tenant_id=uuid.UUID(tenant_id),
            deal_id=deal.id,
            amount=deal.amount,
            currency=arguments.get("currency") or deal.currency,
            customer_email=deal.customer_email,
            idempotency_key=arguments["idempotency_key"],
        )
        provider_execution = result.provider_execution
        execution_result = {
            "provider": result.provider,
            "provider_execution": result.provider_execution,
            "executed": result.executed,
            "checkout_url": result.checkout_url,
            "provider_payment_id": result.provider_payment_id,
        }

    status = "proposal" if external else "draft_or_report"
    approval_status = "approved" if approval_required else "not_required"
    payload = {
        "kind": "sales_operation",
        "sales_id": sales_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "query": arguments.get("query"),
        "criteria": arguments.get("criteria", {}),
        "deal_id": arguments.get("deal_id"),
        "provider_requested": arguments.get("provider", "crm_or_outreach"),
        "provider_execution": provider_execution,
        "external_side_effect": external,
        **({"execution": execution_result} if execution_result is not None else {}),
        "provenance": {
            "tenant_id": tenant_id,
            "created_at": _now(),
            "provider_execution": provider_execution,
        },
    }
    artifact = _save_json(tenant_id, f"sales-{sales_id}.json", payload)
    return {
        **artifact,
        "sales_id": sales_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "provider_execution": provider_execution,
        "external_side_effect": external,
        **({"execution": execution_result} if execution_result is not None else {}),
    }

async def execute_seo_growth(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    """Persist tenant-scoped SEO/growth research and proposals; no search-engine execution."""
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    approval_required = _approval_required("ai_seo_growth_employee", operation)
    external = operation == "seo_experiment_proposal"
    artifact_id = str(uuid.uuid4())
    provider_execution = "not_configured"
    status = "proposal" if external else "research"
    approval_status = "pending" if approval_required else "not_required"
    payload = {
        "kind": "seo_growth_artifact",
        "artifact_id": artifact_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "topic": arguments.get("topic"),
        "query": arguments.get("query"),
        "recommendations": arguments.get("recommendations", []),
        "spec": arguments.get("spec", {}),
        "provider_requested": arguments.get("provider", "search_performance"),
        "provider_execution": provider_execution,
        "external_side_effect": external,
        "provenance": {"tenant_id": tenant_id, "created_at": _now(), "provider_execution": provider_execution},
    }
    artifact = _save_json(tenant_id, f"seo-growth-{artifact_id}.json", payload)
    return {
        **artifact,
        "artifact_id": artifact_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "provider_execution": provider_execution,
        "external_side_effect": external,
    }

async def execute_customer_success(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    approval_required = _approval_required("ai_customer_success", operation)
    external = operation.startswith("send_") or operation.endswith("_proposal")
    artifact_id = str(uuid.uuid4())
    provider_execution = "not_configured"
    status = "proposal" if external else "analysis"
    approval_status = "pending" if approval_required else "not_required"
    payload = {
        "kind": "customer_success_artifact",
        "artifact_id": artifact_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "customer_reference": arguments.get("customer_reference"),
        "query": arguments.get("query"),
        "message": arguments.get("message"),
        "evidence": arguments.get("evidence", []),
        "recommendation": arguments.get("recommendation"),
        "provider_requested": arguments.get("provider", "customer_support"),
        "provider_execution": provider_execution,
        "external_side_effect": external,
        "provenance": {"tenant_id": tenant_id, "created_at": _now(), "provider_execution": provider_execution},
    }
    artifact = _save_json(tenant_id, f"customer-success-{artifact_id}.json", payload)
    return {**artifact, "artifact_id": artifact_id, "operation": operation, "version": 1,
            "status": status, "approval_required": approval_required, "approval_status": approval_status,
            "provider_execution": provider_execution, "external_side_effect": external}


async def execute_qa_devops(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    """Persist tenant-scoped QA/DevOps evidence and governed proposals; no deployment executes here."""
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    approval_required = _approval_required("ai_qa_devops", operation)
    external = operation.endswith("_proposal")
    artifact_id = str(uuid.uuid4())
    provider_execution = "not_configured"
    status = "proposal" if external else "analysis"
    approval_status = "pending" if approval_required else "not_required"
    payload = {
        "kind": "qa_devops_artifact",
        "artifact_id": artifact_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "repository": arguments.get("repository"),
        "commit_sha": arguments.get("commit_sha"),
        "test_scope": arguments.get("test_scope"),
        "finding": arguments.get("finding"),
        "evidence": arguments.get("evidence", []),
        "recommendation": arguments.get("recommendation"),
        "provider_requested": arguments.get("provider", "qa_devops"),
        "provider_execution": provider_execution,
        "external_side_effect": external,
        "provenance": {"tenant_id": tenant_id, "created_at": _now(), "provider_execution": provider_execution},
    }
    artifact = _save_json(tenant_id, f"qa-devops-{artifact_id}.json", payload)
    return {**artifact, "artifact_id": artifact_id, "operation": operation, "version": 1,
            "status": status, "approval_required": approval_required, "approval_status": approval_status,
            "provider_execution": provider_execution, "external_side_effect": external}


async def execute_website(arguments: dict[str, Any], **context: Any) -> dict[str, Any]:
    """Persist tenant-scoped website work; deployment never executes without a provider."""
    tenant_id = _tenant(arguments, context)
    operation = arguments["_operation"]
    change_id = str(uuid.uuid4())
    approval_required = _approval_required("ai_website_employee", operation)
    provider_execution = "not_configured"
    status = "proposal" if approval_required else "staged"
    approval_status = "pending" if approval_required else "not_required"
    payload = {
        "kind": "website_change",
        "change_id": change_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "site": arguments["site"],
        "spec": arguments.get("spec", {}),
        "provider_execution": provider_execution,
        "external_side_effect": operation in {"website_deploy", "website_rollback"},
        "provenance": {"tenant_id": tenant_id, "created_at": _now(), "provider_execution": provider_execution},
    }
    artifact = _save_json(tenant_id, f"website-{change_id}.json", payload)
    return {
        **artifact,
        "change_id": change_id,
        "operation": operation,
        "version": 1,
        "status": status,
        "approval_required": approval_required,
        "approval_status": approval_status,
        "provider_execution": provider_execution,
        "external_side_effect": operation in {"website_deploy", "website_rollback"},
    }