import hashlib
from app.services.api_key_service import KEY_PREFIX


def test_api_key_prefix_and_digest_are_non_reversible_contract():
    secret = KEY_PREFIX + "example-secret"
    digest = hashlib.sha256(secret.encode()).hexdigest()
    assert secret.startswith("aiep_live_")
    assert len(digest) == 64
    assert secret not in digest
