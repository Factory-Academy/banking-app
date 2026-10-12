import pytest

from app.utils.resilience.token_bucket import TokenBucket


class FakeClock:
    """Deterministic, manually advanced monotonic clock for tests."""

    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_starts_full():
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=1, time_func=clock)
    assert bucket.tokens == 5


def test_acquire_consumes_tokens():
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=1, time_func=clock)
    assert bucket.try_acquire(2) is True
    assert bucket.tokens == 3


def test_acquire_fails_when_empty():
    clock = FakeClock()
    bucket = TokenBucket(capacity=2, refill_rate=1, time_func=clock)
    assert bucket.try_acquire(2) is True
    assert bucket.try_acquire(1) is False
    # A failed acquire must not consume anything.
    assert bucket.tokens == 0


def test_refills_over_time():
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=2, time_func=clock)
    assert bucket.try_acquire(5) is True
    assert bucket.try_acquire(1) is False
    clock.advance(1)  # 2 tokens/sec -> 2 tokens
    assert bucket.try_acquire(2) is True
    assert bucket.try_acquire(1) is False


def test_refill_is_capped_at_capacity():
    clock = FakeClock()
    bucket = TokenBucket(capacity=3, refill_rate=1, time_func=clock)
    assert bucket.try_acquire(3) is True
    clock.advance(1000)
    assert bucket.tokens == 3


def test_fractional_refill_accumulates():
    clock = FakeClock()
    bucket = TokenBucket(capacity=10, refill_rate=1, time_func=clock)
    assert bucket.try_acquire(10) is True
    clock.advance(0.5)
    assert bucket.try_acquire(1) is False
    clock.advance(0.5)  # now a full token has accrued
    assert bucket.try_acquire(1) is True


def test_request_larger_than_capacity_never_succeeds():
    clock = FakeClock()
    bucket = TokenBucket(capacity=3, refill_rate=1, time_func=clock)
    assert bucket.try_acquire(4) is False
    clock.advance(1000)
    assert bucket.try_acquire(4) is False


def test_time_until_available_when_ready_is_zero():
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=1, time_func=clock)
    assert bucket.time_until_available(3) == 0.0


def test_time_until_available_computes_wait():
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=2, time_func=clock)
    assert bucket.try_acquire(5) is True
    # Need 3 tokens at 2 tokens/sec -> 1.5 seconds.
    assert bucket.time_until_available(3) == pytest.approx(1.5)


def test_time_until_available_infinite_beyond_capacity():
    clock = FakeClock()
    bucket = TokenBucket(capacity=2, refill_rate=1, time_func=clock)
    assert bucket.time_until_available(3) == float("inf")


def test_backwards_clock_does_not_drain():
    clock = FakeClock(start=100.0)
    bucket = TokenBucket(capacity=5, refill_rate=1, time_func=clock)
    assert bucket.try_acquire(5) is True
    clock.now = 50.0  # clock jumps backwards
    assert bucket.tokens == 0  # unchanged, no spurious refill


@pytest.mark.parametrize("bad_capacity", [0, -1, -5.5])
def test_invalid_capacity_rejected(bad_capacity):
    with pytest.raises(ValueError):
        TokenBucket(capacity=bad_capacity, refill_rate=1)


@pytest.mark.parametrize("bad_rate", [0, -1, -0.5])
def test_invalid_refill_rate_rejected(bad_rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity=5, refill_rate=bad_rate)


@pytest.mark.parametrize("bad_tokens", [0, -1])
def test_non_positive_acquire_rejected(bad_tokens):
    bucket = TokenBucket(capacity=5, refill_rate=1)
    with pytest.raises(ValueError):
        bucket.try_acquire(bad_tokens)


def test_non_positive_time_until_available_rejected():
    bucket = TokenBucket(capacity=5, refill_rate=1)
    with pytest.raises(ValueError):
        bucket.time_until_available(0)


@pytest.mark.parametrize("bad_capacity", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_capacity_rejected(bad_capacity):
    with pytest.raises(ValueError):
        TokenBucket(capacity=bad_capacity, refill_rate=1)


@pytest.mark.parametrize("bad_rate", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_refill_rate_rejected(bad_rate):
    with pytest.raises(ValueError):
        TokenBucket(capacity=5, refill_rate=bad_rate)


@pytest.mark.parametrize("bad_tokens", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_acquire_rejected(bad_tokens):
    # Without an explicit guard, NaN slips past ``tokens <= 0`` and +inf past
    # ``tokens > capacity``, so both must raise rather than silently misbehave.
    bucket = TokenBucket(capacity=5, refill_rate=1)
    with pytest.raises(ValueError):
        bucket.try_acquire(bad_tokens)


def test_non_finite_acquire_does_not_consume():
    clock = FakeClock()
    bucket = TokenBucket(capacity=5, refill_rate=1, time_func=clock)
    with pytest.raises(ValueError):
        bucket.try_acquire(float("nan"))
    assert bucket.tokens == 5


@pytest.mark.parametrize("bad_tokens", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_time_until_available_rejected(bad_tokens):
    bucket = TokenBucket(capacity=5, refill_rate=1)
    with pytest.raises(ValueError):
        bucket.time_until_available(bad_tokens)
