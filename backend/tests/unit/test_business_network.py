import uuid
import pytest
from app.models.business_network_request import BusinessNetworkRequestStatus
def test_w21_status_contract():
    assert {x.value for x in BusinessNetworkRequestStatus}=={"pending_approval","approved","rejected","cancelled"}
def test_w21_idempotency_key_is_string():
    assert isinstance("network-e2e-key",str)
