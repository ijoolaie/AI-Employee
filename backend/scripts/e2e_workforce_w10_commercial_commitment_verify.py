"""Real-stack W10 governed commercial commitment certification.

Uses the existing W10 fixture builder, moves its CRM deal from qualified to
proposal, then executes the approval-gated commercial commitment through the
operator-selected contract-test payment provider. No external payment occurs.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.database import AsyncSessionLocal
from app.models.tool_approval import ToolApprovalRequest
from app.modules.employees.sales import service as sales_service
from scripts.e2e_workforce_w10_dogfood_verify import execute, prepare


async def main() -> None:
    # The parent W10 foundation uses a fixed webhook tenant fixture. This
    # commercial certification must allocate its own tenant so it can run in
    # the same database immediately after the foundation certification.
    os.environ.pop("SALES_INBOUND_TENANT_ID", None)
    tenant_id, instance_id, runs, owner_id, reviewer_id, _ = await prepare()

    deal_call_id = f"w10-commercial-deal-{uuid.uuid4().hex}"
    deal_args = {
        "title": "W10 commercial commitment certification",
        "customer_name": "Commercial Certification Prospect",
        "customer_email": os.environ.get("W10_SALES_RECIPIENT_EMAIL", "prospect@example.invalid").strip(),
        "amount": 250000000,
        "currency": "IRR",
        "stage": "qualified",
        "probability": 25,
        "source": "ai_workforce_commercial_certification",
        "notes": "Certification-only governed commercial commitment fixture.",
    }
    async with AsyncSessionLocal() as db:
        db.add(
            ToolApprovalRequest(
                tenant_id=tenant_id,
                run_id=runs["outreach_draft"],
                tool_name="create_deal",
                tool_call_id=deal_call_id,
                arguments=deal_args,
                continuation_messages=[],
                iteration=0,
                status="approved",
                requested_by=owner_id,
                decided_by=reviewer_id,
                decision_reason="W10 commercial certification: governed CRM fixture",
                decided_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()

    deal = await execute(
        tenant_id,
        instance_id,
        runs["outreach_draft"],
        "create_deal",
        deal_args,
        tool_call_id=deal_call_id,
        actor_id=owner_id,
    )
    deal_id = deal.get("deal_id")
    if not deal_id or deal.get("stage") != "qualified":
        raise RuntimeError(f"Commercial certification deal fixture mismatch: {deal!r}")

    async with AsyncSessionLocal() as db:
        await sales_service.update_stage(
            db,
            tenant_id=tenant_id,
            actor_id=owner_id,
            deal_id=deal_id,
            stage="proposal",
        )
        await db.commit()

    commercial_call_id = f"w10-commercial-action-{uuid.uuid4().hex}"
    commercial_args = {
        "deal_id": deal_id,
        "currency": "IRR",
        "payment_amount": 250000000,
        "idempotency_key": commercial_call_id,
    }
    async with AsyncSessionLocal() as db:
        db.add(
            ToolApprovalRequest(
                tenant_id=tenant_id,
                run_id=runs["external_outreach"],
                tool_name="workforce_material_commercial_action",
                tool_call_id=commercial_call_id,
                arguments=commercial_args,
                continuation_messages=[],
                iteration=0,
                status="approved",
                requested_by=owner_id,
                decided_by=reviewer_id,
                decision_reason="W10 commercial certification: approved governed commitment",
                decided_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()

    result = await execute(
        tenant_id,
        instance_id,
        runs["external_outreach"],
        "workforce_material_commercial_action",
        commercial_args,
        tool_call_id=commercial_call_id,
        actor_id=owner_id,
    )

    assert result["approval_required"] is True
    assert result["approval_status"] == "approved"
    assert result["external_side_effect"] is True
    assert result["provider_execution"] == "accepted"
    assert result["execution"]["provider"] == "contract-test"
    assert result["execution"]["executed"] is False
    assert result["execution"]["checkout_url"]
    assert result["execution"]["provider_payment_id"].startswith("contract-payment-")
    assert result["deal_id"] == deal_id

    async with AsyncSessionLocal() as db:
        deal_row = await sales_service.get_deal(db, tenant_id=tenant_id, deal_id=deal_id)
        assert deal_row.stage == "proposal"
        assert deal_row.amount == 250000000
        assert deal_row.currency == "IRR"

    print("W10 GOVERNED COMMERCIAL COMMITMENT PASS provider=contract-test")
    print("W10 COMMERCIAL EXTERNAL PAYMENT NOT_RUN: contract-test provider is non-external")
    print("W10 REVENUE OUTCOME NOT_VERIFIED: no verified customer payment/revenue event")


if __name__ == "__main__":
    asyncio.run(main())
