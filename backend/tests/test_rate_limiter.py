import threading

import pytest

from app.utils.resilience import RateLimiter, RateLimitResult


class FakeClock:
    """Deterministic, manually advanced monotonic clock for tests."""

    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_allow_within_burst():
    clock = FakeClock()
    limiter = RateLimiter(capacity=3, refill_rate=1, time_func=clock)
    results = [limiter.allow("acct-1") for _ in range(3)]
    assert all(r.allowed for r in results)
    assert results[-1].remaining == 0


def test_allow_blocks_after_burst():
    clock = FakeClock()
    limiter = RateLimiter(capacity=2, refill_rate=1, time_func=clock)
    assert limiter.allow("acct-1").allowed is True
    assert limiter.allow("acct-1").allowed is True
    denied = limiter.allow("acct-1")
    assert denied.allowed is False
    assert denied.remaining == 0
    assert denied.retry_after == pytest.approx(1.0)
    assert denied.limit == 2


def test_result_is_truthy():
    limiter = RateLimiter(capacity=1, refill_rate=1)
    result = limiter.allow("acct-1")
    assert isinstance(result, RateLimitResult)
    assert bool(result) is True
    assert bool(limiter.allow("acct-1")) is False


def test_keys_are_independent():
    clock = FakeClock()
    limiter = RateLimiter(capacity=1, refill_rate=1, time_func=clock)
    assert limiter.allow("acct-1").allowed is True
    # A different account still has its full allowance.
    assert limiter.allow("acct-2").allowed is True
    assert limiter.allow("acct-1").allowed is False


def test_recovers_after_refill():
    clock = FakeClock()
    limiter = RateLimiter(capacity=1, refill_rate=1, time_func=clock)
    assert limiter.allow("acct-1").allowed is True
    assert limiter.allow("acct-1").allowed is False
    clock.advance(1)
    assert limiter.allow("acct-1").allowed is True


def test_peek_does_not_consume():
    clock = FakeClock()
    limiter = RateLimiter(capacity=2, refill_rate=1, time_func=clock)
    before = limiter.peek("acct-1")
    assert before.allowed is True
    assert before.remaining == 2
    # Peeking repeatedly must not drain the bucket.
    assert limiter.peek("acct-1").remaining == 2
    assert limiter.allow("acct-1").allowed is True


def test_reset_restores_allowance():
    clock = FakeClock()
    limiter = RateLimiter(capacity=1, refill_rate=1, time_func=clock)
    assert limiter.allow("acct-1").allowed is True
    assert limiter.allow("acct-1").allowed is False
    limiter.reset("acct-1")
    assert limiter.allow("acct-1").allowed is True


def test_reset_all():
    limiter = RateLimiter(capacity=1, refill_rate=1)
    limiter.allow("acct-1")
    limiter.allow("acct-2")
    assert limiter.active_keys == 2
    limiter.reset_all()
    assert limiter.active_keys == 0


def test_cost_greater_than_one():
    clock = FakeClock()
    limiter = RateLimiter(capacity=5, refill_rate=1, time_func=clock)
    assert limiter.allow("acct-1", cost=3).allowed is True
    assert limiter.allow("acct-1", cost=3).allowed is False


def test_cost_beyond_capacity_denied_with_infinite_retry():
    limiter = RateLimiter(capacity=2, refill_rate=1)
    result = limiter.allow("acct-1", cost=5)
    assert result.allowed is False
    assert result.retry_after == float("inf")


def test_prune_removes_idle_buckets():
    clock = FakeClock()
    limiter = RateLimiter(capacity=5, refill_rate=1, time_func=clock)
    limiter.allow("acct-1")
    limiter.allow("acct-2")
    clock.advance(100)
    # Touch acct-2 so it is no longer idle.
    limiter.allow("acct-2")
    removed = limiter.prune(max_idle_seconds=50)
    assert removed == 1
    assert limiter.active_keys == 1


def test_prune_rejects_negative():
    limiter = RateLimiter(capacity=1, refill_rate=1)
    with pytest.raises(ValueError):
        limiter.prune(-1)


@pytest.mark.parametrize("bad_key", [None, ""])
def test_empty_key_rejected(bad_key):
    limiter = RateLimiter(capacity=1, refill_rate=1)
    with pytest.raises(ValueError):
        limiter.allow(bad_key)


@pytest.mark.parametrize("bad_capacity", [0, -1])
def test_invalid_capacity_rejected(bad_capacity):
    with pytest.raises(ValueError):
        RateLimiter(capacity=bad_capacity, refill_rate=1)


@pytest.mark.parametrize("bad_rate", [0, -1])
def test_invalid_refill_rate_rejected(bad_rate):
    with pytest.raises(ValueError):
        RateLimiter(capacity=1, refill_rate=bad_rate)


def test_concurrent_access_never_oversells():
    # With real wall-clock refill this would be racy, so freeze time: exactly
    # `capacity` acquisitions must succeed across many competing threads.
    clock = FakeClock()
    limiter = RateLimiter(capacity=50, refill_rate=1, time_func=clock)
    successes = []
    lock = threading.Lock()

    def worker():
        if limiter.allow("acct-1").allowed:
            with lock:
                successes.append(1)

    threads = [threading.Thread(target=worker) for _ in range(200)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(successes) == 50
