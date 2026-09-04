from app.services.tenant_fair_scheduler import TenantFairScheduler


class FakeStore:
    def __init__(self):
        self.values = {}
        self.scores = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, **kwargs):
        self.values[key] = value

    def zscore(self, key, member):
        return self.scores.get(key, {}).get(member)

    def zadd(self, key, mapping):
        self.scores.setdefault(key, {}).update(mapping)

    def zrange(self, key, start, end, withscores=False):
        rows = sorted(self.scores.get(key, {}).items(), key=lambda item: (item[1], item[0]))
        rows = rows[start : end + 1]
        return rows if withscores else [member for member, _ in rows]


def test_scheduler_rejects_missing_or_invalid_tenant_configuration():
    scheduler = TenantFairScheduler(FakeStore())

    for tenant_id in ("", "   "):
        try:
            scheduler.route(tenant_id)
        except ValueError:
            pass
        else:
            raise AssertionError("empty tenant id must be rejected")

    try:
        scheduler.route("tenant-a", weight=0)
    except ValueError:
        pass
    else:
        raise AssertionError("non-positive weight must be rejected")


def test_equal_weight_tenants_keep_virtual_finish_fairness():
    scheduler = TenantFairScheduler(FakeStore())
    decisions = [scheduler.route("a" if i % 2 == 0 else "b") for i in range(20)]

    assert [d.virtual_finish for d in decisions[::2]] == list(range(1.0, 11.0))
    assert [d.virtual_finish for d in decisions[1::2]] == list(range(1.0, 11.0))
    assert all(0 <= d.queue_priority <= 9 for d in decisions)


def test_busy_tenant_loses_priority_to_new_tenant():
    scheduler = TenantFairScheduler(FakeStore())
    first = scheduler.route("busy")
    scheduler.route("busy")
    scheduler.route("busy")
    newcomer = scheduler.route("new")

    assert newcomer.virtual_finish < first.virtual_finish + 3
    assert newcomer.queue_priority <= first.queue_priority


def test_weighted_tenant_advances_faster_but_remains_bounded():
    scheduler = TenantFairScheduler(FakeStore())
    light = scheduler.route("light", weight=1.0)
    heavy = scheduler.route("heavy", weight=2.0)

    assert heavy.virtual_finish == 0.5
    assert light.virtual_finish == 1.0
    assert 0 <= heavy.queue_priority <= 9
    assert 0 <= light.queue_priority <= 9
