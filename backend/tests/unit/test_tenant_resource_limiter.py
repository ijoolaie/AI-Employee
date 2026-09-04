from app.services.tenant_resource_limiter import TenantResourceLimiter


class FakeRedis:
    def __init__(self):
        self.slots = {}

    def eval(self, script, numkeys, key, *args):
        if "ZCARD" in script:
            expires_at, now, limit, token = args
            current = {t: expiry for t, expiry in self.slots.get(key, {}).items() if expiry > float(now)}
            self.slots[key] = current
            if len(current) >= int(limit):
                return 0
            current[token] = float(expires_at)
            return 1
        token = args[0]
        return int(self.slots.get(key, {}).pop(token, None) is not None)


def test_default_and_tenant_specific_limits_are_selected():
    limiter = TenantResourceLimiter(FakeRedis(), {"tenant-a": 2}, default_limit=1, lease_seconds=60)
    assert limiter.limit_for("tenant-a") == 2
    assert limiter.limit_for("tenant-b") == 1


def test_acquire_and_release_enforce_tenant_concurrency():
    redis = FakeRedis()
    limiter = TenantResourceLimiter(redis, {}, default_limit=1, lease_seconds=60)

    first = limiter.acquire("tenant-a")
    second = limiter.acquire("tenant-a")
    other = limiter.acquire("tenant-b")

    assert first is not None
    assert second is None
    assert other is not None

    limiter.release(first)
    assert limiter.acquire("tenant-a") is not None


def test_different_tenants_do_not_consume_each_others_share():
    limiter = TenantResourceLimiter(FakeRedis(), {"tenant-a": 1, "tenant-b": 2}, default_limit=1, lease_seconds=60)

    assert limiter.acquire("tenant-a") is not None
    assert limiter.acquire("tenant-b") is not None
    assert limiter.acquire("tenant-b") is not None
    assert limiter.acquire("tenant-b") is None
