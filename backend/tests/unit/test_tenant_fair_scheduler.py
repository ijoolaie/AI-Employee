from app.services.tenant_fair_scheduler import TenantFairScheduler


class FakeStore:
    def __init__(self):
        self.clock = {}
        self.scores = {}

    def reserve(self, score_key, clock_key, tenant_id, weight):
        scores = self.scores.setdefault(score_key, {})
        was_new = tenant_id not in scores
        current = float(scores.get(tenant_id, 0.0))
        clock = float(self.clock.get(clock_key, 0.0))
        start = max(current, clock)
        finish = start + (1.0 / weight)
        scores[tenant_id] = finish
        frontier_score = min(scores.values()) if scores else finish
        self.clock[clock_key] = frontier_score
        return finish, frontier_score, was_new


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


def test_busy_tenant_does_not_starve_newcomer():
    scheduler = TenantFairScheduler(FakeStore())
    first = scheduler.route("busy")
    scheduler.route("busy")
    scheduler.route("busy")
    newcomer = scheduler.route("new")

    assert newcomer.virtual_finish == 4.0
    assert newcomer.queue_priority == 0
    assert newcomer.queue_priority <= first.queue_priority


def test_new_tenant_gets_starvation_protection_priority():
    scheduler = TenantFairScheduler(FakeStore())
    scheduler.route("busy")
    scheduler.route("busy")
    newcomer = scheduler.route("new")

    assert newcomer.queue_priority == 0


def test_weighted_tenant_gets_smaller_virtual_finish_increment():
    scheduler = TenantFairScheduler(FakeStore())
    light = scheduler.route("light", weight=1.0)
    heavy = scheduler.route("heavy", weight=2.0)

    assert light.virtual_finish == 1.0
    assert heavy.virtual_finish == 1.5
    assert heavy.virtual_finish - light.virtual_finish == 0.5
    assert 0 <= heavy.queue_priority <= 9
    assert 0 <= light.queue_priority <= 9
