from decimal import Decimal

import pytest

from app.core.exceptions import ValidationAppError
from app.services.skill_marketplace_settlement_service import _calculate_split


def test_marketplace_split_calculates_fee_and_seller_net_exactly():
    fee, seller_net = _calculate_split(Decimal("100.00"), 1500)
    assert fee == Decimal("15.00")
    assert seller_net == Decimal("85.00")


def test_marketplace_split_rounds_half_up_to_currency_precision():
    fee, seller_net = _calculate_split(Decimal("19.99"), 333)
    assert fee == Decimal("0.67")
    assert seller_net == Decimal("19.32")


@pytest.mark.parametrize("fee_bps", [-1, 10001])
def test_marketplace_split_rejects_invalid_fee_policy(fee_bps):
    with pytest.raises(ValidationAppError):
        _calculate_split(Decimal("10.00"), fee_bps)


def test_marketplace_split_rejects_non_positive_gross():
    with pytest.raises(ValidationAppError):
        _calculate_split(Decimal("0.00"), 1500)
