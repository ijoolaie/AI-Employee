"""Controlled Tool Registry and execution boundary.

Tools are registered by code, exposed to the model only when explicitly allowed
by the immutable EmployeeVersion, and executed only through this registry.
The registry now includes the first side-effecting external integration: `send_email`.
It is fail-closed by configuration, requires `run.execute`, and always requires
human approval before execution.
"""

from __future__ import annotations

import ast
import operator
import smtplib
import time
from email.message import EmailMessage
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from jsonschema import Draft202012Validator

from app.ai.schemas import ToolDefinition
from app.core.config import get_settings
from app.core.exceptions import ValidationAppError


@dataclass(frozen=True)
class RegisteredTool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Any]
    side_effects: bool = False
    required_permission: str = "run.execute"
    requires_approval: bool = False

    @property
    def entitlement_code(self) -> str | None:
        """Commercial entitlement code for tenant-scoped business tools.

        Local utility tools remain free of commercial entitlement gating.
        Business tools use a stable name-derived code so licenses can restrict
        capabilities without coupling the registry to a plan implementation.
        """
        if self.name in {"calculator", "current_time"}:
            return None
        return f"tool:{self.name}"

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, tool: RegisteredTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> RegisteredTool:
        tool = self._tools.get(name)
        if tool is None:
            raise ValidationAppError(
                f"Tool is not registered: {name}",
                details={"tool": name},
            )
        return tool

    def list(self) -> list[RegisteredTool]:
        return list(self._tools.values())

    def definitions_for(self, allowed_tools: list[str]) -> list[ToolDefinition]:
        definitions: list[ToolDefinition] = []
        for name in allowed_tools:
            definitions.append(self.get(name).definition)
        return definitions

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        permissions: set[str] | None = None,
        approval_granted: bool = False,
        allowed_tools: set[str] | list[str] | None = None,
        db=None,
        tenant_id=None,
        actor_id=None,
    ) -> Any:
        tool = self.get(name)

        # Commercial entitlement is enforced at the real execution boundary
        # when a tenant Run supplies transactional DB and tenant context.
        if tool.entitlement_code is not None and db is not None and tenant_id is not None:
            from app.services import license_service

            await license_service.assert_feature_entitlement(
                db,
                tenant_id=tenant_id,
                feature_code=tool.entitlement_code,
            )

        # Employee guardrail is a separate, fail-closed capability boundary.
        # A tool must be both declared by the EmployeeVersion and permitted
        # for the executing principal. Tool visibility in the prompt is not
        # sufficient because provider output is untrusted.
        if allowed_tools is not None and name not in set(allowed_tools):
            raise ValidationAppError(
                f"Tool is not allowed by Employee guardrails: {name}",
                details={
                    "tool": name,
                    "allowed_tools": sorted(set(allowed_tools)),
                },
            )

        permissions = permissions or set()
        if tool.required_permission not in permissions:
            raise ValidationAppError(
                f"Missing permission for tool: {name}",
                details={"tool": name, "required_permission": tool.required_permission},
            )
        if tool.requires_approval and not approval_granted:
            raise ValidationAppError(
                f"Human approval required for tool: {name}",
                details={"tool": name, "approval_required": True},
            )
        validator = Draft202012Validator(tool.input_schema)
        errors = sorted(validator.iter_errors(arguments), key=lambda e: list(e.path))
        if errors:
            raise ValidationAppError(
                f"Invalid arguments for tool '{name}'",
                details={
                    "tool": name,
                    "errors": [
                        {"path": list(error.path), "message": error.message}
                        for error in errors[:10]
                    ],
                },
            )
        started = time.perf_counter()
        if name == "send_email":
            settings = get_settings()
            allowed_domains = {
                d.strip().lower().lstrip("@")
                for d in settings.smtp_allowed_recipient_domains
                if d.strip()
            }

            # Fail closed before touching any persistence layer. This keeps the
            # security boundary deterministic even when no transactional DB
            # context is available (for example during local tool execution).
            if not settings.smtp_host or not settings.smtp_from_email or not allowed_domains:
                raise ValidationAppError(
                    "Email integration is not configured or allowlist is empty; fail-closed"
                )

            for address in arguments["to"]:
                if "@" not in address:
                    raise ValidationAppError(
                        "Recipient domain is not allowed",
                        details={"recipient": address},
                    )
                domain = address.rsplit("@", 1)[1].lower()
                if domain not in allowed_domains:
                    raise ValidationAppError(
                        "Recipient domain is not allowed",
                        details={"recipient": address},
                    )

            # With a transactional context, enqueue the email for durable
            # post-commit dispatch. Without one, execute the already-approved
            # SMTP side effect directly; this path is primarily useful for
            # isolated/local tool execution and unit tests.
            if db is not None and tenant_id is not None:
                from app.services.outbox_service import enqueue

                queued = await enqueue(
                    db,
                    kind="email.send",
                    tenant_id=tenant_id,
                    payload={
                        "to": arguments["to"],
                        "subject": arguments["subject"],
                        "body": arguments["body"],
                    },
                )
                result = {
                    "queued": True,
                    "outbox_id": str(queued.id),
                    "recipient_count": len(arguments["to"]),
                    "subject": arguments["subject"],
                }
            else:
                message = EmailMessage()
                message["From"] = settings.smtp_from_email
                message["To"] = ", ".join(arguments["to"])
                message["Subject"] = arguments["subject"]
                message.set_content(arguments["body"])
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                    if settings.smtp_use_starttls:
                        smtp.starttls()
                    if settings.smtp_username:
                        smtp.login(settings.smtp_username, settings.smtp_password or "")
                    smtp.send_message(message)
                result = {
                    "sent": True,
                    "recipient_count": len(arguments["to"]),
                    "subject": arguments["subject"],
                }
        elif name == "analyze_dataset":
            # Requires DB + tenant context, same as send_email above. This is
            # the Phase 2 "Report Employee" analysis path (report_service.py);
            # never reachable without a Run's TenantContext.
            if db is None or tenant_id is None:
                raise ValidationAppError(
                    "analyze_dataset requires an active tenant Run context"
                )
            from app.services import report_service

            result = await report_service.analyze_dataset(
                db,
                tenant_id=tenant_id,
                actor_id=None,
                file_id=arguments["file_id"],
            )
        elif name == "analyze_document":
            # Requires DB + tenant context, same as analyze_dataset above.
            # This is the Phase 5 "Document Employee" analysis path
            # (document_service.py); never reachable without a Run's
            # TenantContext.
            if db is None or tenant_id is None:
                raise ValidationAppError(
                    "analyze_document requires an active tenant Run context"
                )
            from app.services import document_service

            result = await document_service.analyze_document(
                db,
                tenant_id=tenant_id,
                actor_id=None,
                file_id=arguments["file_id"],
            )

        elif name in {
            "workforce_market_research",
            "workforce_market_trading_plan",
            "workforce_market_risk_analysis",
            "workforce_prepare_ceo_report",
            "workforce_prepare_growth_report", "workforce_draft_campaign_plan", "workforce_coordinate_content", "workforce_request_capacity", "workforce_prepare_cost_optimization", "workforce_prepare_budget_estimate",
        }:
            result = await tool.handler(
                arguments,
                db=db,
                tenant_id=tenant_id,
            )
        elif name == "create_invoice":
            if db is None or tenant_id is None:
                raise ValidationAppError("create_invoice requires an active tenant Run context")
            from app.services import invoice_service
            inv = await invoice_service.create_invoice(
                db,
                tenant_id=tenant_id,
                actor_id=actor_id,
                customer_name=arguments["customer_name"],
                line_items=arguments["line_items"],
                currency=arguments.get("currency", "IRR"),
                tax_rate=arguments.get("tax_rate", 0),
                number=arguments.get("number"),
                customer_email=arguments.get("customer_email"),
                notes=arguments.get("notes"),
                source_file_id=arguments.get("source_file_id"),
            )
            result = {
                "invoice_id": str(inv.id),
                "number": inv.number,
                "status": inv.status,
                "total": float(inv.total),
                "currency": inv.currency,
                "subtotal": float(inv.subtotal),
                "tax_amount": float(inv.tax_amount),
            }
        elif name == "update_invoice_status":
            if db is None or tenant_id is None:
                raise ValidationAppError("update_invoice_status requires an active tenant Run context")
            from app.services import invoice_service
            inv = await invoice_service.update_status(
                db,
                tenant_id=tenant_id,
                actor_id=actor_id,
                invoice_id=arguments["invoice_id"],
                status=arguments["status"],
            )
            result = {"invoice_id": str(inv.id), "status": inv.status, "number": inv.number}
        elif name == "analyze_invoice_file":
            if db is None or tenant_id is None:
                raise ValidationAppError("analyze_invoice_file requires an active tenant Run context")
            from app.services import invoice_service
            result = await invoice_service.analyze_invoice_file(
                db, tenant_id=tenant_id, actor_id=actor_id, file_id=arguments["file_id"]
            )
        elif name == "export_invoice_pdf":
            if db is None or tenant_id is None:
                raise ValidationAppError("export_invoice_pdf requires an active tenant Run context")
            from app.services import invoice_service
            result = await invoice_service.export_pdf(
                db, tenant_id=tenant_id, actor_id=actor_id, invoice_id=arguments["invoice_id"]
            )
        elif name == "invoice_financial_summary":
            if db is None or tenant_id is None:
                raise ValidationAppError("invoice_financial_summary requires an active tenant Run context")
            from app.services import invoice_service
            result = await invoice_service.financial_summary(db, tenant_id=tenant_id)

        elif name == "create_order":
            if db is None or tenant_id is None:
                raise ValidationAppError("create_order requires an active tenant Run context")
            from app.services import order_service
            order = await order_service.create_order(
                db,
                tenant_id=tenant_id,
                actor_id=actor_id,
                customer_name=arguments["customer_name"],
                line_items=arguments["line_items"],
                currency=arguments.get("currency", "IRR"),
                tax_rate=arguments.get("tax_rate", 0),
                number=arguments.get("number"),
                customer_email=arguments.get("customer_email"),
                notes=arguments.get("notes"),
                source_file_id=arguments.get("source_file_id"),
                invoice_id=arguments.get("invoice_id"),
            )
            result = {
                "order_id": str(order.id),
                "number": order.number,
                "status": order.status,
                "total": float(order.total),
                "currency": order.currency,
                "subtotal": float(order.subtotal),
                "tax_amount": float(order.tax_amount),
            }
        elif name == "get_order":
            if db is None or tenant_id is None:
                raise ValidationAppError("get_order requires an active tenant Run context")
            from app.services import order_service
            order = await order_service.find_order_for_customer(db, tenant_id=tenant_id, order_id=arguments.get("order_id"), order_number=arguments.get("order_number"))
            result = {"order_id": str(order.id), "number": order.number, "status": order.status, "total": float(order.total), "currency": order.currency, "customer_name": order.customer_name, "customer_email": order.customer_email, "line_items": order.line_items}
        elif name == "track_order":
            if db is None or tenant_id is None:
                raise ValidationAppError("track_order requires an active tenant Run context")
            from app.services import order_service
            order = await order_service.find_order_for_customer(db, tenant_id=tenant_id, order_id=arguments.get("order_id"), order_number=arguments.get("order_number"))
            result = {"order_id": str(order.id), "number": order.number, "status": order.status, "requested_delivery_date": order.requested_delivery_date.isoformat() if order.requested_delivery_date else None, "message": f"Order {order.number} is currently {order.status}."}
        elif name == "update_order_status":
            if db is None or tenant_id is None:
                raise ValidationAppError("update_order_status requires an active tenant Run context")
            from app.services import order_service
            order = await order_service.update_status(
                db,
                tenant_id=tenant_id,
                actor_id=actor_id,
                order_id=arguments["order_id"],
                status=arguments["status"],
            )
            result = {"order_id": str(order.id), "status": order.status, "number": order.number}
        elif name == "analyze_order_file":
            if db is None or tenant_id is None:
                raise ValidationAppError("analyze_order_file requires an active tenant Run context")
            from app.services import order_service
            result = await order_service.analyze_order_file(
                db, tenant_id=tenant_id, actor_id=actor_id, file_id=arguments["file_id"]
            )
        elif name == "order_summary":
            if db is None or tenant_id is None:
                raise ValidationAppError("order_summary requires an active tenant Run context")
            from app.services import order_service
            result = await order_service.order_summary(db, tenant_id=tenant_id)

        elif name == "create_deal":
            if db is None or tenant_id is None:
                raise ValidationAppError("create_deal requires an active tenant Run context")
            from app.services import sales_service
            deal = await sales_service.create_deal(
                db,
                tenant_id=tenant_id,
                actor_id=actor_id,
                title=arguments["title"],
                customer_name=arguments["customer_name"],
                amount=arguments.get("amount", 0),
                currency=arguments.get("currency", "IRR"),
                stage=arguments.get("stage", "lead"),
                probability=arguments.get("probability"),
                customer_email=arguments.get("customer_email"),
                notes=arguments.get("notes"),
                source=arguments.get("source"),
                order_id=arguments.get("order_id"),
            )
            result = {
                "deal_id": str(deal.id),
                "title": deal.title,
                "stage": deal.stage,
                "amount": float(deal.amount),
                "currency": deal.currency,
                "probability": deal.probability,
            }
        elif name == "update_deal_stage":
            if db is None or tenant_id is None:
                raise ValidationAppError("update_deal_stage requires an active tenant Run context")
            from app.services import sales_service
            deal = await sales_service.update_stage(
                db,
                tenant_id=tenant_id,
                actor_id=actor_id,
                deal_id=arguments["deal_id"],
                stage=arguments["stage"],
                probability=arguments.get("probability"),
            )
            result = {
                "deal_id": str(deal.id),
                "stage": deal.stage,
                "probability": deal.probability,
                "title": deal.title,
            }
        elif name == "sales_pipeline_summary":
            if db is None or tenant_id is None:
                raise ValidationAppError("sales_pipeline_summary requires an active tenant Run context")
            from app.services import sales_service
            result = await sales_service.pipeline_summary(db, tenant_id=tenant_id)
        elif name == "sales_forecast":
            if db is None or tenant_id is None:
                raise ValidationAppError("sales_forecast requires an active tenant Run context")
            from app.services import sales_service
            result = await sales_service.simple_forecast(
                db,
                tenant_id=tenant_id,
                horizon_days=int(arguments.get("horizon_days", 30)),
            )
        elif name == "link_order_invoice":
            if db is None or tenant_id is None:
                raise ValidationAppError("link_order_invoice requires an active tenant Run context")
            from app.services import order_service
            order = await order_service.link_invoice(
                db,
                tenant_id=tenant_id,
                actor_id=actor_id,
                order_id=arguments["order_id"],
                invoice_id=arguments["invoice_id"],
            )
            result = {
                "order_id": str(order.id),
                "invoice_id": str(order.invoice_id) if order.invoice_id else None,
                "number": order.number,
            }
        elif name == "search_products":
            result = await _search_products(arguments, db=db, tenant_id=tenant_id, actor_id=actor_id)
        elif name == "get_product":
            result = await _get_product(arguments, db=db, tenant_id=tenant_id, actor_id=actor_id)
        elif name == "check_inventory":
            result = await _check_inventory(arguments, db=db, tenant_id=tenant_id, actor_id=actor_id)
        else:
            result = tool.handler(arguments)
        if hasattr(result, "__await__"):
            result = await result
        _ = time.perf_counter() - started
        return result


def _calculator(arguments: dict[str, Any]) -> dict[str, Any]:
    expression = arguments["expression"]
    tree = ast.parse(expression, mode="eval")

    binary_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    unary_ops = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    def evaluate(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
            left = evaluate(node.left)
            right = evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent is too large")
            value = binary_ops[type(node.op)](left, right)
            if abs(value) > 1e100:
                raise ValueError("Result is too large")
            return value
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary_ops:
            return unary_ops[type(node.op)](evaluate(node.operand))
        raise ValueError("Only numeric arithmetic expressions are allowed")

    try:
        value = evaluate(tree.body)
    except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as exc:
        raise ValidationAppError(
            "Invalid calculator expression",
            details={"tool": "calculator", "message": str(exc)},
        ) from exc
    return {"expression": expression, "result": value}


def _current_time(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"utc": datetime.now(timezone.utc).isoformat()}



def _send_email(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError("Direct SMTP execution is disabled; email is queued through the transactional outbox.")


def _analyze_dataset(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "analyze_dataset requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _analyze_document(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "analyze_document requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


async def _workforce_market_risk_analysis(arguments: dict[str, Any], **context):
    tenant_id = context.get("tenant_id")
    if context.get("db") is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_market_risk_analysis requires an active tenant Run context"
        )
    from app.services.workforce_market_risk_analysis_service import risk_analysis
    return await risk_analysis(
        tenant_id=tenant_id,
        symbols=arguments["symbols"],
        horizon_days=int(arguments.get("horizon_days", 30)),
    )


async def _workforce_market_trading_plan(arguments: dict[str, Any], **context):
    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_market_trading_plan requires an active tenant Run context"
        )
    from app.services.workforce_market_trading_plan_service import prepare_trading_plan
    return await prepare_trading_plan(
        tenant_id=tenant_id,
        symbols=arguments["symbols"],
        horizon_days=int(arguments.get("horizon_days", 30)),
        objective=arguments.get("objective", "balanced"),
    )




async def _workforce_request_capacity(arguments: dict[str, Any], **context):
    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_request_capacity requires an active tenant Run context"
        )
    from app.services import capacity_forecasting

    forecast = await capacity_forecasting.capacity_forecast(
        db,
        tenant_id=tenant_id,
        window_days=arguments.get("window_days", 30),
        horizon_days=arguments.get("horizon_days", 7),
    )
    return {
        "tenant_id": str(forecast.tenant_id),
        "window_days": forecast.window_days,
        "horizon_days": forecast.horizon_days,
        "sample_count": forecast.sample_count,
        "demand_samples_per_day": forecast.demand_samples_per_day,
        "average_run_duration_seconds": forecast.average_run_duration_seconds,
        "current_ready_items": forecast.current_ready_items,
        "current_active_work_items": forecast.current_active_work_items,
        "total_max_concurrency": forecast.total_max_concurrency,
        "total_available_slots": forecast.total_available_slots,
        "projected_arrivals": forecast.projected_arrivals,
        "projected_required_concurrency": forecast.projected_required_concurrency,
        "projected_utilization": forecast.projected_utilization,
        "projected_backlog": forecast.projected_backlog,
        "lower_bound_required_concurrency": forecast.lower_bound_required_concurrency,
        "upper_bound_required_concurrency": forecast.upper_bound_required_concurrency,
        "evidence_complete": forecast.evidence_complete,
        "rationale": forecast.rationale,
        "contract_version": forecast.contract_version,
        "window_start": forecast.window_start.isoformat(),
        "window_end": forecast.window_end.isoformat(),
    }


async def _workforce_prepare_budget_estimate(arguments: dict[str, Any], **context):
    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_prepare_budget_estimate requires an active tenant Run context"
        )
    from app.services import optimization_service

    estimate = await optimization_service.tenant_budget_estimate(
        db,
        tenant_id=tenant_id,
    )
    estimate["period_start"] = estimate["period_start"].isoformat()
    return estimate


async def _workforce_prepare_cost_optimization(arguments: dict[str, Any], **context):
    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_prepare_cost_optimization requires an active tenant Run context"
        )
    from app.services import optimization_service

    summary = await optimization_service.tenant_optimization_summary(
        db,
        tenant_id=tenant_id,
    )
    return {
        **summary,
        "period_start": summary["period_start"].isoformat(),
    }


async def _workforce_prepare_ceo_report(arguments: dict[str, Any], **context):
    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_prepare_ceo_report requires an active tenant Run context"
        )
    from app.services.agent_workforce_manager import get_workforce_dashboard

    window_days = int(arguments.get("window_days", 30))
    return await get_workforce_dashboard(
        db,
        tenant_id=tenant_id,
        window_days=window_days,
    )

async def _workforce_coordinate_content(arguments: dict[str, Any], **context):
    tenant_id = context.get("tenant_id")
    if context.get("db") is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_coordinate_content requires an active tenant Run context"
        )
    from app.services.workforce_marketing_content_coordination_service import coordinate_content

    return coordinate_content(
        tenant_id=str(tenant_id),
        objective=arguments["objective"],
        channels=arguments["channels"],
        audience=arguments["audience"],
        key_message=arguments["key_message"],
        offer=arguments.get("offer"),
    )


async def _workforce_draft_campaign_plan(arguments: dict[str, Any], **context):
    tenant_id = context.get("tenant_id")
    if context.get("db") is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_draft_campaign_plan requires an active tenant Run context"
        )
    from app.services.workforce_marketing_campaign_plan_service import draft_campaign_plan

    return draft_campaign_plan(
        tenant_id=str(tenant_id),
        objective=arguments["objective"],
        audience=arguments["audience"],
        channels=arguments["channels"],
        duration_days=int(arguments.get("duration_days", 30)),
        budget=arguments.get("budget"),
        offer=arguments.get("offer"),
    )


async def _workforce_prepare_growth_report(arguments: dict[str, Any], **context):
    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_prepare_growth_report requires an active tenant Run context"
        )
    from app.services.workforce_marketing_growth_report_service import prepare_growth_report

    return await prepare_growth_report(
        db,
        tenant_id=tenant_id,
        window_days=int(arguments.get("window_days", 30)),
    )


async def _workforce_market_research(arguments: dict[str, Any], **context):
    db = context.get("db")
    tenant_id = context.get("tenant_id")
    if db is None or tenant_id is None:
        raise ValidationAppError(
            "workforce_market_research requires an active tenant Run context"
        )
    from app.services.workforce_market_research_service import market_research
    return await market_research(
        tenant_id=tenant_id,
        symbols=arguments["symbols"],
        horizon_days=int(arguments.get("horizon_days", 30)),
    )


def _create_invoice(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "create_invoice requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _update_invoice_status(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "update_invoice_status requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _analyze_invoice_file(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "analyze_invoice_file requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _export_invoice_pdf(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "export_invoice_pdf requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _invoice_financial_summary(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "invoice_financial_summary requires a tenant Run context and is executed via ToolRegistry.execute()."
    )

def _create_order(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "create_order requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _get_order(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError("get_order requires a tenant Run context and is executed via ToolRegistry.execute().")

def _track_order(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError("track_order requires a tenant Run context and is executed via ToolRegistry.execute().")


def _update_order_status(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "update_order_status requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _analyze_order_file(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "analyze_order_file requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _order_summary(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "order_summary requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _link_order_invoice(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "link_order_invoice requires a tenant Run context and is executed via ToolRegistry.execute()."
    )

def _create_deal(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "create_deal requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _update_deal_stage(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "update_deal_stage requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _sales_pipeline_summary(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "sales_pipeline_summary requires a tenant Run context and is executed via ToolRegistry.execute()."
    )


def _sales_forecast(arguments: dict[str, Any]) -> dict[str, Any]:
    raise ValidationAppError(
        "sales_forecast requires a tenant Run context and is executed via ToolRegistry.execute()."
    )




async def _search_products(arguments: dict[str, Any], **context):
    db = context.get("db"); tenant_id = context.get("tenant_id")
    if db is None or tenant_id is None: raise ValidationAppError("search_products requires an active tenant Run context")
    from app.services import product_service
    rows = await product_service.list_products(db, tenant_id, arguments.get("query"), active_only=True)
    return [{"id": str(p.id), "sku": p.sku, "name": p.name, "price": float(p.price), "currency": p.currency, "inventory": p.inventory, "category": p.category, "attributes": p.attributes} for p in rows[:arguments.get("limit", 10)]]

async def _get_product(arguments: dict[str, Any], **context):
    db = context.get("db"); tenant_id = context.get("tenant_id")
    if db is None or tenant_id is None: raise ValidationAppError("get_product requires an active tenant Run context")
    from sqlalchemy import select
    from app.models.product import Product
    from uuid import UUID
    p = (await db.execute(select(Product).where(Product.id == UUID(arguments["product_id"]), Product.tenant_id == tenant_id, Product.is_active.is_(True)))).scalar_one_or_none()
    if not p: raise ValidationAppError("Product not found")
    return {"id": str(p.id), "sku": p.sku, "name": p.name, "description": p.description, "price": float(p.price), "currency": p.currency, "inventory": p.inventory, "attributes": p.attributes}

async def _check_inventory(arguments: dict[str, Any], **context):
    product = await _get_product(arguments, **context)
    return {"product_id": product["id"], "name": product["name"], "inventory": product["inventory"], "available": product["inventory"] > 0}

def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        RegisteredTool(
            name="calculator",
            description="Evaluate a safe numeric arithmetic expression. No variables, imports, or code execution.",
            input_schema={
                "type": "object",
                "properties": {"expression": {"type": "string", "minLength": 1, "maxLength": 200}},
                "required": ["expression"],
                "additionalProperties": False,
            },
            handler=_calculator,
            side_effects=False,
        )
    )
    registry.register(
        RegisteredTool(
            name="current_time",
            description="Return the current UTC time from the application worker.",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            handler=_current_time,
            side_effects=False,
        )
    )
    registry.register(
        RegisteredTool(
            name="send_email",
            description="Send an email through the configured SMTP integration. Requires explicit human approval.",
            input_schema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "array",
                        "items": {"type": "string", "format": "email"},
                        "minItems": 1,
                        "maxItems": 10,
                        "uniqueItems": True,
                    },
                    "subject": {"type": "string", "minLength": 1, "maxLength": 200},
                    "body": {"type": "string", "minLength": 1, "maxLength": 10000},
                },
                "required": ["to", "subject", "body"],
                "additionalProperties": False,
            },
            handler=_send_email,
            side_effects=True,
            required_permission="run.execute",
            requires_approval=True,
        )
    )
    registry.register(
        RegisteredTool(
            name="analyze_dataset",
            description=(
                "Analyze a previously-uploaded tenant CSV/Excel file: compute row/column KPIs, "
                "numeric summaries, category breakdowns, a simple trend forecast when a date "
                "column is present, render charts, and produce a downloadable PDF + Excel report. "
                "Returns file IDs for the generated report artifacts."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "ID of a file previously uploaded via the Files API (CSV or Excel).",
                    }
                },
                "required": ["file_id"],
                "additionalProperties": False,
            },
            handler=_analyze_dataset,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )
    registry.register(
        RegisteredTool(
            name="analyze_document",
            description=(
                "Analyze a previously-uploaded tenant PDF, image (PNG/JPEG), or DOCX file: "
                "extract text (using OCR — English + Persian — for scanned pages), classify it "
                "as a contract/letter/form/administrative document, and detect common fields "
                "(dates, monetary amounts, emails, phone numbers, ID-number candidates). "
                "Returns a file ID for the full extracted text."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "ID of a file previously uploaded via the Files API (PDF, PNG/JPEG, DOCX, or TXT).",
                    }
                },
                "required": ["file_id"],
                "additionalProperties": False,
            },
            handler=_analyze_document,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_market_trading_plan",
            description="Read-only trading-plan preparation through the operator-configured market provider. It never places orders or allocates capital.",
            input_schema={
                "type": "object",
                "properties": {
                    "symbols": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 32}, "minItems": 1, "maxItems": 20, "uniqueItems": True},
                    "horizon_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30},
                    "objective": {"type": "string", "enum": ["conservative", "balanced", "growth"], "default": "balanced"},
                },
                "required": ["symbols"],
                "additionalProperties": False,
            },
            handler=_workforce_market_trading_plan,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_market_risk_analysis",
            description="Read-only market risk analysis from the operator-configured provider. No order placement, capital allocation, leverage, withdrawal, or external trading side effects.",
            input_schema={
                "type": "object",
                "properties": {
                    "symbols": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 32}, "minItems": 1, "maxItems": 20, "uniqueItems": True},
                    "horizon_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30},
                },
                "required": ["symbols"],
                "additionalProperties": False,
            },
            handler=_workforce_market_risk_analysis,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_market_research",
            description=(
                "Read-only market research through the operator-configured market-data provider. "
                "No order placement, capital allocation, leverage, withdrawal, or other trading side effect."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "symbols": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1, "maxLength": 32},
                        "minItems": 1,
                        "maxItems": 20,
                        "uniqueItems": True,
                    },
                    "horizon_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30},
                },
                "required": ["symbols"],
                "additionalProperties": False,
            },
            handler=_workforce_market_research,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_request_capacity",
            description="Read-only tenant-scoped workforce capacity forecast for the Internal Manager; reports demand and capacity evidence without scaling or lifecycle side effects.",
            input_schema={
                "type": "object",
                "properties": {
                    "window_days": {"type": "integer", "minimum": 1, "maximum": 90, "default": 30},
                    "horizon_days": {"type": "integer", "minimum": 1, "maximum": 30, "default": 7},
                },
                "additionalProperties": False,
            },
            handler=_workforce_request_capacity,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_prepare_budget_estimate",
            description="Read-only tenant-scoped month-end usage budget estimate from measured plan consumption; not accounting or financial commitment advice.",
            input_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            handler=_workforce_prepare_budget_estimate,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_prepare_cost_optimization",
            description="Read-only tenant-scoped workforce cost optimization guidance using measured usage, budget state and unit economics; no financial commitment or resource change.",
            input_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            handler=_workforce_prepare_cost_optimization,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_prepare_ceo_report",
            description="Read-only tenant-scoped workforce dashboard prepared for Internal Manager CEO reporting; no staffing, financial, or execution side effects.",
            input_schema={
                "type": "object",
                "properties": {
                    "window_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30},
                },
                "additionalProperties": False,
            },
            handler=_workforce_prepare_ceo_report,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_coordinate_content",
            description="Read-only tenant-scoped marketing content work package; plans channel deliverables without publishing or external side effects.",
            input_schema={
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "minLength": 1, "maxLength": 500},
                    "channels": {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 100}, "minItems": 1, "maxItems": 20, "uniqueItems": True},
                    "audience": {"type": "string", "minLength": 1, "maxLength": 500},
                    "key_message": {"type": "string", "minLength": 1, "maxLength": 2000},
                    "offer": {"type": "string", "maxLength": 1000},
                },
                "required": ["objective", "channels", "audience", "key_message"],
                "additionalProperties": False,
            },
            handler=_workforce_coordinate_content,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_draft_campaign_plan",
            description="Read-only tenant-scoped draft campaign plan for the AI Marketing Manager; planning only, with no campaign launch, external spend, or external-system side effects.",
            input_schema={
                "type": "object",
                "properties": {
                    "objective": {"type": "string", "minLength": 1, "maxLength": 500},
                    "audience": {"type": "string", "minLength": 1, "maxLength": 500},
                    "channels": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1, "maxLength": 100},
                        "minItems": 1,
                        "maxItems": 20,
                        "uniqueItems": True,
                    },
                    "duration_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30},
                    "budget": {"type": "number", "minimum": 0},
                    "offer": {"type": "string", "maxLength": 1000},
                },
                "required": ["objective", "audience", "channels"],
                "additionalProperties": False,
            },
            handler=_workforce_draft_campaign_plan,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="workforce_prepare_growth_report",
            description="Read-only tenant-scoped commercial growth report for the AI Marketing Manager, based on orders and sales pipeline; no campaign attribution or external spend side effects.",
            input_schema={
                "type": "object",
                "properties": {
                    "window_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30},
                },
                "additionalProperties": False,
            },
            handler=_workforce_prepare_growth_report,
            side_effects=False,
            required_permission="run.execute",
            requires_approval=False,
        )
    )

    registry.register(
        RegisteredTool(
            name="create_invoice",
            description="Create a structured business invoice (line items, tax, currency) for the current tenant.",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "minLength": 1, "maxLength": 255},
                    "customer_email": {"type": "string"},
                    "currency": {"type": "string", "minLength": 3, "maxLength": 8},
                    "tax_rate": {"type": "number", "minimum": 0, "maximum": 100, "description": "Tax as percent points (e.g. 9 for 9%). Values in (0,1] are treated as fractions (0.09 -> 9%)."},
                    "number": {"type": "string", "maxLength": 64},
                    "notes": {"type": "string"},
                    "source_file_id": {"type": "string", "format": "uuid"},
                    "line_items": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                            },
                            "required": ["description", "unit_price"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["customer_name", "line_items"],
                "additionalProperties": False,
            },
            handler=_create_invoice,
            side_effects=True,
            required_permission="run.execute",
            requires_approval=False,
        )
    )
    registry.register(
        RegisteredTool(
            name="update_invoice_status",
            description="Update business invoice status: draft|sent|paid|overdue|void.",
            input_schema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "string", "format": "uuid"},
                    "status": {"type": "string", "enum": ["draft", "sent", "paid", "overdue", "void"]},
                },
                "required": ["invoice_id", "status"],
                "additionalProperties": False,
            },
            handler=_update_invoice_status,
            side_effects=True,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="analyze_invoice_file",
            description="Analyze an uploaded invoice file and extract number/amount/date/email candidates.",
            input_schema={
                "type": "object",
                "properties": {"file_id": {"type": "string", "format": "uuid"}},
                "required": ["file_id"],
                "additionalProperties": False,
            },
            handler=_analyze_invoice_file,
            side_effects=False,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="export_invoice_pdf",
            description="Render a business invoice to PDF and store it as a tenant file.",
            input_schema={
                "type": "object",
                "properties": {"invoice_id": {"type": "string", "format": "uuid"}},
                "required": ["invoice_id"],
                "additionalProperties": False,
            },
            handler=_export_invoice_pdf,
            side_effects=True,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="invoice_financial_summary",
            description="Summarize outstanding vs collected amounts for the tenant business invoices.",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            handler=_invoice_financial_summary,
            side_effects=False,
            required_permission="run.execute",
        )
    )


    registry.register(
        RegisteredTool(
            name="create_order",
            description="Create a structured business order (line items, tax, currency) for the current tenant.",
            input_schema={
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "minLength": 1, "maxLength": 255},
                    "customer_email": {"type": "string"},
                    "currency": {"type": "string", "minLength": 3, "maxLength": 8},
                    "tax_rate": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Tax as percent points (e.g. 9 for 9%). Values in (0,1] treated as fractions.",
                    },
                    "number": {"type": "string", "maxLength": 64},
                    "notes": {"type": "string"},
                    "source_file_id": {"type": "string", "format": "uuid"},
                    "invoice_id": {"type": "string", "format": "uuid"},
                    "line_items": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                                "sku": {"type": "string"},
                            },
                            "required": ["description", "unit_price"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["customer_name", "line_items"],
                "additionalProperties": False,
            },
            handler=_create_order,
            side_effects=True,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="get_order",
            description="Retrieve a tenant order by internal order ID or customer-visible order number.",
            input_schema={"type":"object","properties":{"order_id":{"type":"string","format":"uuid"},"order_number":{"type":"string","minLength":1,"maxLength":64}},"anyOf":[{"required":["order_id"]},{"required":["order_number"]}],"additionalProperties":False},
            handler=lambda arguments: _get_order(arguments), side_effects=False, required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="track_order",
            description="Return the current status and delivery information for a tenant order.",
            input_schema={"type":"object","properties":{"order_id":{"type":"string","format":"uuid"},"order_number":{"type":"string","minLength":1,"maxLength":64}},"anyOf":[{"required":["order_id"]},{"required":["order_number"]}],"additionalProperties":False},
            handler=lambda arguments: _track_order(arguments), side_effects=False, required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="update_order_status",
            description="Update business order status: draft|confirmed|processing|shipped|delivered|cancelled.",
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "format": "uuid"},
                    "status": {
                        "type": "string",
                        "enum": ["draft", "confirmed", "processing", "shipped", "delivered", "cancelled"],
                    },
                },
                "required": ["order_id", "status"],
                "additionalProperties": False,
            },
            handler=_update_order_status,
            side_effects=True,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="analyze_order_file",
            description="Analyze an uploaded order/PO file and extract number/amount/date/email candidates.",
            input_schema={
                "type": "object",
                "properties": {"file_id": {"type": "string", "format": "uuid"}},
                "required": ["file_id"],
                "additionalProperties": False,
            },
            handler=_analyze_order_file,
            side_effects=False,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="order_summary",
            description="Summarize open vs delivered vs cancelled order totals for the tenant.",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            handler=_order_summary,
            side_effects=False,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="link_order_invoice",
            description="Link a business order to an existing business invoice in the same tenant.",
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "format": "uuid"},
                    "invoice_id": {"type": "string", "format": "uuid"},
                },
                "required": ["order_id", "invoice_id"],
                "additionalProperties": False,
            },
            handler=_link_order_invoice,
            side_effects=True,
            required_permission="run.execute",
        )
    )


    registry.register(
        RegisteredTool(
            name="create_deal",
            description="Create a sales deal/opportunity with stage, amount, and win probability.",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "minLength": 1, "maxLength": 255},
                    "customer_name": {"type": "string", "minLength": 1, "maxLength": 255},
                    "customer_email": {"type": "string"},
                    "amount": {"type": "number", "minimum": 0},
                    "currency": {"type": "string", "minLength": 3, "maxLength": 8},
                    "stage": {
                        "type": "string",
                        "enum": ["lead", "qualified", "proposal", "negotiation", "won", "lost"],
                    },
                    "probability": {"type": "integer", "minimum": 0, "maximum": 100},
                    "notes": {"type": "string"},
                    "source": {"type": "string"},
                    "order_id": {"type": "string", "format": "uuid"},
                },
                "required": ["title", "customer_name"],
                "additionalProperties": False,
            },
            handler=_create_deal,
            side_effects=True,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="update_deal_stage",
            description="Update deal stage: lead|qualified|proposal|negotiation|won|lost.",
            input_schema={
                "type": "object",
                "properties": {
                    "deal_id": {"type": "string", "format": "uuid"},
                    "stage": {
                        "type": "string",
                        "enum": ["lead", "qualified", "proposal", "negotiation", "won", "lost"],
                    },
                    "probability": {"type": "integer", "minimum": 0, "maximum": 100},
                },
                "required": ["deal_id", "stage"],
                "additionalProperties": False,
            },
            handler=_update_deal_stage,
            side_effects=True,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="sales_pipeline_summary",
            description="Summarize sales pipeline by stage, weighted pipeline, won/lost amounts.",
            input_schema={"type": "object", "properties": {}, "additionalProperties": False},
            handler=_sales_pipeline_summary,
            side_effects=False,
            required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="sales_forecast",
            description="Simple probability-weighted revenue forecast for open deals within a horizon.",
            input_schema={
                "type": "object",
                "properties": {
                    "horizon_days": {"type": "integer", "minimum": 1, "maximum": 365, "default": 30},
                },
                "additionalProperties": False,
            },
            handler=_sales_forecast,
            side_effects=False,
            required_permission="run.execute",
        )
    )

    registry.register(
        RegisteredTool(
            name="search_products",
            description="Search the tenant product catalog for customer-facing product recommendations.",
            input_schema={"type":"object","properties":{"query":{"type":"string"},"limit":{"type":"integer","minimum":1,"maximum":20}},"required":["query"],"additionalProperties":False},
            handler=_search_products, side_effects=False, required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="get_product",
            description="Get a product's price, attributes and current inventory.",
            input_schema={"type":"object","properties":{"product_id":{"type":"string","format":"uuid"}},"required":["product_id"],"additionalProperties":False},
            handler=_get_product, side_effects=False, required_permission="run.execute",
        )
    )
    registry.register(
        RegisteredTool(
            name="check_inventory",
            description="Check whether a product is currently in stock.",
            input_schema={"type":"object","properties":{"product_id":{"type":"string","format":"uuid"}},"required":["product_id"],"additionalProperties":False},
            handler=_check_inventory, side_effects=False, required_permission="run.execute",
        )
    )

    return registry


registry = build_default_registry()
