from uuid import uuid4

import pytest

from app.core.exceptions import ValidationAppError
from app.services.skill_marketplace_payout_destination import _validate_destination


def test_destination_validation_normalizes_provider_and_reference():
    provider, destination = _validate_destination(
        provider="  CONTRACT-TEST ",
        destination_ref="  provider-account-123  ",
    )
    assert provider == "contract-test"
    assert destination == "provider-account-123"


@pytest.mark.parametrize(
    ("provider", "destination_ref"),
    [
        ("", "destination"),
        ("x" * 41, "destination"),
        ("contract-test", ""),
        ("contract-test", "x" * 256),
        ("contract-test", "destination\n"),
    ],
)
def test_destination_validation_rejects_invalid_values(provider, destination_ref):
    with pytest.raises(ValidationAppError):
        _validate_destination(provider=provider, destination_ref=destination_ref)


def test_destination_model_uses_tenant_and_actor_fields():
    from app.models.skill_marketplace_payout_destination import (
        SkillMarketplacePayoutDestination,
        SkillMarketplacePayoutDestinationStatus,
    )

    seller = uuid4()
    actor = uuid4()
    binding = SkillMarketplacePayoutDestination(
        seller_tenant_id=seller,
        provider="contract-test",
        destination_ref="provider-account-1",
        created_by_user_id=actor,
    )
    assert binding.seller_tenant_id == seller
    assert binding.created_by_user_id == actor
    assert binding.status == SkillMarketplacePayoutDestinationStatus.ACTIVE


def test_destination_service_has_no_external_transport_import():
    from pathlib import Path

    path = Path(__file__).parents[1] / "app/services/skill_marketplace_payout_destination.py"
    content = path.read_text(encoding="utf-8")
    assert "httpx" not in content
    assert "urllib" not in content
    assert "requests" not in content
    assert "stripe" not in content
