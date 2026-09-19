import random

import pytest

from app.utils.resilience import (
    BackoffPolicy,
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    MaxRetriesExceededError,
    ResilientCaller,
    resilient,
)


class FakeClock:
    """A manually advanced monotonic clock for deterministic time control."""

    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class RecordingSleeper:
    """A drop-in for time.sleep that records the delays it was asked to wait."""

    def __init__(self):
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


class FlakyCallable:
    """Callable that fails a fixed number of times before succeeding."""

    def __init__(self, fail_times: int, exc: Exception, result="ok"):
        self.fail_times = fail_times
        self.exc = exc
        self.result = result
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.exc
        return self.result


class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


# --------------------------------------------------------------------------- #
# BackoffPolicy
# --------------------------------------------------------------------------- #


class TestBackoffPolicy:
    def test_exponential_growth_without_jitter(self):
        policy = BackoffPolicy(base_delay=1.0, multiplier=2.0, max_delay=100.0, jitter=False)
        assert policy.compute_delay(1) == 1.0
        assert policy.compute_delay(2) == 2.0
        assert policy.compute_delay(3) == 4.0
        assert policy.compute_delay(4) == 8.0

    def test_delay_capped_at_max(self):
        policy = BackoffPolicy(base_delay=1.0, multiplier=10.0, max_delay=5.0, jitter=False)
        assert policy.compute_delay(1) == 1.0
        assert policy.compute_delay(2) == 5.0  # 10 capped
        assert policy.compute_delay(5) == 5.0

    def test_jitter_stays_within_bounds(self):
        policy = BackoffPolicy(base_delay=1.0, multiplier=2.0, max_delay=100.0, jitter=True)
        rng = random.Random(1234)
        for attempt in range(1, 6):
            ceiling = min(1.0 * 2 ** (attempt - 1), 100.0)
            for _ in range(50):
                delay = policy.compute_delay(attempt, rng)
                assert 0.0 <= delay <= ceiling

    def test_jitter_is_deterministic_with_seeded_rng(self):
        policy = BackoffPolicy(jitter=True)
        a = policy.compute_delay(2, random.Random(7))
        b = policy.compute_delay(2, random.Random(7))
        assert a == b

    def test_zero_base_delay_is_allowed(self):
        policy = BackoffPolicy(base_delay=0.0, jitter=False)
        assert policy.compute_delay(1) == 0.0
        assert policy.compute_delay(5) == 0.0

    def test_zero_base_delay_never_becomes_nan_for_large_attempt(self):
        # 0.0 * (multiplier ** huge) would be 0 * inf == nan without a guard.
        policy = BackoffPolicy(base_delay=0.0, multiplier=2.0, jitter=False)
        assert policy.compute_delay(5000) == 0.0

    def test_large_attempt_caps_at_max_delay_without_overflow(self):
        # multiplier ** (attempt - 1) overflows float range for large attempts;
        # compute_delay must return the cap rather than raise OverflowError.
        policy = BackoffPolicy(base_delay=0.5, multiplier=2.0, max_delay=8.0, jitter=False)
        assert policy.compute_delay(5000) == 8.0

    def test_large_attempt_caps_at_max_delay_with_jitter(self):
        policy = BackoffPolicy(base_delay=0.5, multiplier=2.0, max_delay=8.0, jitter=True)
        rng = random.Random(99)
        for _ in range(50):
            delay = policy.compute_delay(5000, rng)
            assert 0.0 <= delay <= 8.0

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"max_attempts": 0},
            {"base_delay": -1},
            {"max_delay": -1},
            {"multiplier": 0.5},
            {"base_delay": 10, "max_delay": 5},
        ],
    )
    def test_invalid_configuration_rejected(self, kwargs):
        with pytest.raises(ValueError):
            BackoffPolicy(**kwargs)

    def test_attempt_must_be_positive(self):
        with pytest.raises(ValueError):
            BackoffPolicy(jitter=False).compute_delay(0)


# --------------------------------------------------------------------------- #
# CircuitBreaker
# --------------------------------------------------------------------------- #


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker()
        assert cb.state is CircuitState.CLOSED

    def test_trips_open_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state is CircuitState.CLOSED
        cb.record_failure()
        assert cb.state is CircuitState.OPEN

    def test_open_rejects_calls(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        with pytest.raises(CircuitBreakerOpenError):
            cb.check()

    def test_success_resets_failure_count_while_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0
        # Needs a full new run of failures to trip.
        cb.record_failure()
        cb.record_failure()
        assert cb.state is CircuitState.CLOSED

    def test_recovers_to_half_open_after_timeout(self):
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10.0, time_func=clock)
        cb.record_failure()
        assert cb.state is CircuitState.OPEN

        clock.advance(9.0)
        assert cb.state is CircuitState.OPEN  # not yet
        clock.advance(1.0)
        assert cb.state is CircuitState.HALF_OPEN

    def test_half_open_success_closes(self):
        clock = FakeClock()
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=5.0,
            success_threshold=2,
            half_open_max_calls=2,
            time_func=clock,
        )
        cb.record_failure()
        clock.advance(5.0)
        assert cb.state is CircuitState.HALF_OPEN

        cb.check()
        cb.record_success()
        assert cb.state is CircuitState.HALF_OPEN  # one more needed
        cb.check()
        cb.record_success()
        assert cb.state is CircuitState.CLOSED

    def test_half_open_failure_reopens(self):
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=5.0, time_func=clock)
        cb.record_failure()
        clock.advance(5.0)
        assert cb.state is CircuitState.HALF_OPEN

        cb.check()
        cb.record_failure()
        assert cb.state is CircuitState.OPEN

    def test_half_open_limits_trial_calls(self):
        clock = FakeClock()
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=5.0,
            half_open_max_calls=1,
            time_func=clock,
        )
        cb.record_failure()
        clock.advance(5.0)

        cb.check()  # consumes the single trial slot
        with pytest.raises(CircuitBreakerOpenError):
            cb.check()

    def test_retry_after_is_reported(self):
        clock = FakeClock()
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=10.0, time_func=clock)
        cb.record_failure()
        clock.advance(3.0)
        try:
            cb.check()
        except CircuitBreakerOpenError as e:
            assert e.retry_after == pytest.approx(7.0)
        else:
            pytest.fail("expected CircuitBreakerOpenError")

    def test_manual_reset(self):
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        assert cb.state is CircuitState.OPEN
        cb.reset()
        assert cb.state is CircuitState.CLOSED

    def test_release_frees_a_reserved_half_open_slot(self):
        clock = FakeClock()
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=5.0,
            half_open_max_calls=1,
            time_func=clock,
        )
        cb.record_failure()
        clock.advance(5.0)
        assert cb.state is CircuitState.HALF_OPEN

        cb.check()  # reserve the only trial slot
        cb.release()  # outcome never recorded -> give the slot back
        cb.check()  # slot is available again rather than starved forever

    def test_release_is_a_noop_when_closed(self):
        cb = CircuitBreaker(failure_threshold=2)
        cb.release()  # nothing reserved; must not raise or corrupt state
        assert cb.state is CircuitState.CLOSED
        cb.record_failure()
        assert cb.failure_count == 1

    def test_half_open_recovers_when_max_calls_below_success_threshold(self):
        # With one trial slot but two required successes, the slot must be
        # freed after each success so the second probe can proceed; otherwise
        # the breaker would be permanently stuck half-open.
        clock = FakeClock()
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=5.0,
            success_threshold=2,
            half_open_max_calls=1,
            time_func=clock,
        )
        cb.record_failure()
        clock.advance(5.0)
        assert cb.state is CircuitState.HALF_OPEN

        cb.check()
        cb.record_success()
        assert cb.state is CircuitState.HALF_OPEN

        cb.check()  # slot freed by the previous success
        cb.record_success()
        assert cb.state is CircuitState.CLOSED

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"failure_threshold": 0},
            {"recovery_timeout": -1},
            {"success_threshold": 0},
            {"half_open_max_calls": 0},
        ],
    )
    def test_invalid_configuration_rejected(self, kwargs):
        with pytest.raises(ValueError):
            CircuitBreaker(**kwargs)


# --------------------------------------------------------------------------- #
# ResilientCaller
# --------------------------------------------------------------------------- #


def make_caller(**overrides) -> tuple[ResilientCaller, RecordingSleeper]:
    sleeper = RecordingSleeper()
    defaults = dict(
        policy=BackoffPolicy(max_attempts=3, base_delay=1.0, multiplier=2.0, jitter=False),
        breaker=CircuitBreaker(failure_threshold=100),  # effectively disabled
        retryable_exceptions=(TransientError,),
        sleep_func=sleeper,
    )
    defaults.update(overrides)
    return ResilientCaller(**defaults), sleeper


class TestResilientCaller:
    def test_returns_result_on_first_success(self):
        caller, sleeper = make_caller()
        func = FlakyCallable(fail_times=0, exc=TransientError())
        assert caller.call(func) == "ok"
        assert func.calls == 1
        assert sleeper.calls == []

    def test_passes_through_args_and_kwargs(self):
        caller, _ = make_caller()

        def add(a, b, c=0):
            return a + b + c

        assert caller.call(add, 1, 2, c=3) == 6

    def test_retries_then_succeeds(self):
        caller, sleeper = make_caller()
        func = FlakyCallable(fail_times=2, exc=TransientError())
        assert caller.call(func) == "ok"
        assert func.calls == 3
        # Two backoff waits between three attempts.
        assert sleeper.calls == [1.0, 2.0]

    def test_exhausts_retries_and_wraps_last_exception(self):
        caller, sleeper = make_caller()
        boom = TransientError("still broken")
        func = FlakyCallable(fail_times=10, exc=boom)

        with pytest.raises(MaxRetriesExceededError) as info:
            caller.call(func)

        assert info.value.attempts == 3
        assert info.value.last_exception is boom
        assert info.value.__cause__ is boom
        assert func.calls == 3
        assert sleeper.calls == [1.0, 2.0]

    def test_non_retryable_exception_propagates_immediately(self):
        caller, sleeper = make_caller()
        func = FlakyCallable(fail_times=10, exc=PermanentError("nope"))

        with pytest.raises(PermanentError):
            caller.call(func)

        assert func.calls == 1
        assert sleeper.calls == []

    def test_non_retryable_exception_does_not_count_against_breaker(self):
        breaker = CircuitBreaker(failure_threshold=1)
        caller, _ = make_caller(breaker=breaker)
        func = FlakyCallable(fail_times=10, exc=PermanentError())

        with pytest.raises(PermanentError):
            caller.call(func)

        assert breaker.state is CircuitState.CLOSED

    def test_non_retryable_in_half_open_releases_trial_slot(self):
        # A non-transient error escapes without being recorded against the
        # breaker. The half-open trial slot it reserved must still be freed so
        # a genuine recovery probe can follow.
        clock = FakeClock()
        breaker = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=5.0,
            half_open_max_calls=1,
            time_func=clock,
        )
        breaker.record_failure()
        clock.advance(5.0)
        assert breaker.state is CircuitState.HALF_OPEN

        caller, _ = make_caller(breaker=breaker)

        def boom():
            raise PermanentError("not transient")

        with pytest.raises(PermanentError):
            caller.call(boom)

        # The slot is available again: a follow-up trial call is admitted and
        # can succeed, closing the breaker.
        assert caller.call(lambda: "ok") == "ok"
        assert breaker.state is CircuitState.CLOSED

    def test_jitter_delays_use_injected_rng(self):
        sleeper = RecordingSleeper()
        caller = ResilientCaller(
            policy=BackoffPolicy(max_attempts=3, base_delay=4.0, multiplier=2.0, jitter=True),
            breaker=CircuitBreaker(failure_threshold=100),
            retryable_exceptions=(TransientError,),
            sleep_func=sleeper,
            rng=random.Random(42),
        )
        func = FlakyCallable(fail_times=2, exc=TransientError())
        caller.call(func)

        expected_ceilings = [4.0, 8.0]
        assert len(sleeper.calls) == 2
        for waited, ceiling in zip(sleeper.calls, expected_ceilings):
            assert 0.0 <= waited <= ceiling

    def test_open_breaker_rejects_before_calling(self):
        breaker = CircuitBreaker(failure_threshold=1)
        breaker.record_failure()  # trip it
        caller, _ = make_caller(breaker=breaker)

        called = {"count": 0}

        def func():
            called["count"] += 1
            return "ok"

        with pytest.raises(CircuitBreakerOpenError):
            caller.call(func)
        assert called["count"] == 0

    def test_breaker_trips_mid_retry_and_surfaces_real_cause(self):
        # Threshold of 2 with 5 attempts: the breaker trips after two failures,
        # so retrying stops early and the underlying error is surfaced.
        boom = TransientError("dependency down")
        caller, sleeper = make_caller(
            policy=BackoffPolicy(max_attempts=5, base_delay=1.0, jitter=False),
            breaker=CircuitBreaker(failure_threshold=2),
        )
        func = FlakyCallable(fail_times=10, exc=boom)

        with pytest.raises(MaxRetriesExceededError) as info:
            caller.call(func)

        assert info.value.last_exception is boom
        assert func.calls == 2  # stopped once the breaker opened

    def test_empty_retryable_exceptions_rejected(self):
        with pytest.raises(ValueError):
            ResilientCaller(retryable_exceptions=())

    def test_timeout_style_exception_is_retried(self):
        # A stand-in for a client timeout: it is transient and should retry.
        class TimeoutLike(TransientError):
            pass

        caller, sleeper = make_caller(retryable_exceptions=(TimeoutLike,))
        func = FlakyCallable(fail_times=1, exc=TimeoutLike("timed out"))
        assert caller.call(func) == "ok"
        assert func.calls == 2


# --------------------------------------------------------------------------- #
# resilient decorator
# --------------------------------------------------------------------------- #


class TestResilientDecorator:
    def test_decorator_retries(self):
        sleeper = RecordingSleeper()
        state = {"calls": 0}

        @resilient(
            policy=BackoffPolicy(max_attempts=3, base_delay=1.0, jitter=False),
            retryable_exceptions=(TransientError,),
            sleep_func=sleeper,
        )
        def flaky():
            state["calls"] += 1
            if state["calls"] < 3:
                raise TransientError()
            return "done"

        assert flaky() == "done"
        assert state["calls"] == 3

    def test_decorator_preserves_metadata(self):
        @resilient(retryable_exceptions=(TransientError,))
        def documented():
            """A docstring."""
            return 1

        assert documented.__name__ == "documented"
        assert documented.__doc__ == "A docstring."

    def test_decorator_shares_single_breaker(self):
        sleeper = RecordingSleeper()

        @resilient(
            policy=BackoffPolicy(max_attempts=1, jitter=False),
            breaker=CircuitBreaker(failure_threshold=2),
            retryable_exceptions=(TransientError,),
            sleep_func=sleeper,
        )
        def always_fails():
            raise TransientError()

        # Each call is a single attempt; breaker state must persist across calls.
        with pytest.raises(MaxRetriesExceededError):
            always_fails()
        with pytest.raises(MaxRetriesExceededError):
            always_fails()
        # Breaker has now seen two failures and is open.
        with pytest.raises(CircuitBreakerOpenError):
            always_fails()

        assert always_fails.resilient_caller.breaker.state is CircuitState.OPEN
