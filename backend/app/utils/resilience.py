"""Retry-with-backoff and circuit-breaker utilities.

Small, dependency-free building blocks for making outbound calls (HTTP
clients, database drivers, third-party SDKs) tolerant of transient failures:

- :class:`BackoffPolicy` computes exponential backoff delays with optional
  full jitter.
- :class:`CircuitBreaker` trips open after repeated failures so a struggling
  dependency is given time to recover instead of being hammered.
- :class:`ResilientCaller` combines the two behind a single ``call`` method,
  and :func:`resilient` exposes the same behavior as a decorator.

The module relies only on the standard library. Time and randomness are
injectable (``time_func``, ``sleep_func``, ``rng``) so behavior is fully
deterministic under test.
"""

from __future__ import annotations

import functools
import logging
import random
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Tuple, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Shared source of jitter used when a caller does not supply its own RNG.
_DEFAULT_RNG = random.Random()


class ResilienceError(Exception):
    """Base class for errors raised by this module."""


class CircuitBreakerOpenError(ResilienceError):
    """Raised when a call is rejected because the circuit breaker is open."""

    def __init__(self, retry_after: Optional[float] = None) -> None:
        self.retry_after = retry_after
        message = "circuit breaker is open"
        if retry_after is not None:
            message += f"; retry after {retry_after:.2f}s"
        super().__init__(message)


class MaxRetriesExceededError(ResilienceError):
    """Raised when every retry attempt has been exhausted.

    The exception that caused the final attempt to fail is preserved on
    :attr:`last_exception` (and chained via ``raise ... from``) so callers can
    branch on the underlying cause.
    """

    def __init__(self, attempts: int, last_exception: BaseException) -> None:
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(
            f"call failed after {attempts} attempt(s): {last_exception!r}"
        )


@dataclass(frozen=True)
class BackoffPolicy:
    """Configuration for exponential backoff with optional full jitter.

    The delay applied *after* a failed attempt ``n`` (1-based) is::

        raw   = base_delay * (multiplier ** (n - 1))
        delay = min(raw, max_delay)

    When ``jitter`` is enabled the delay is drawn uniformly from
    ``[0, delay]`` (the "full jitter" strategy), which spreads out retries
    from many clients and avoids synchronized thundering-herd bursts.
    """

    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 30.0
    multiplier: float = 2.0
    jitter: bool = True

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.max_delay < 0:
            raise ValueError("max_delay must be >= 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.multiplier < 1:
            raise ValueError("multiplier must be >= 1")

    def compute_delay(
        self, attempt: int, rng: Optional[random.Random] = None
    ) -> float:
        """Return the delay in seconds to wait after failed ``attempt``.

        ``attempt`` is 1-based: pass ``1`` for the delay following the first
        failed attempt. The returned value is always non-negative and never
        exceeds :attr:`max_delay`.
        """
        if attempt < 1:
            raise ValueError("attempt must be >= 1")

        raw = self.base_delay * (self.multiplier ** (attempt - 1))
        delay = min(raw, self.max_delay)

        if self.jitter:
            source = rng if rng is not None else _DEFAULT_RNG
            delay = source.uniform(0, delay)

        return delay


class CircuitState(str, Enum):
    """Lifecycle states of a :class:`CircuitBreaker`."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """A thread-safe circuit breaker.

    States:

    - ``CLOSED``: calls flow through. Consecutive failures are counted; once
      they reach ``failure_threshold`` the breaker trips to ``OPEN``.
    - ``OPEN``: calls are rejected immediately with
      :class:`CircuitBreakerOpenError`. After ``recovery_timeout`` seconds the
      breaker moves to ``HALF_OPEN``.
    - ``HALF_OPEN``: a limited number of trial calls (``half_open_max_calls``)
      are allowed through. ``success_threshold`` consecutive successes close
      the breaker; any failure reopens it.

    Time is read through ``time_func`` (defaults to :func:`time.monotonic`) so
    recovery timing can be driven deterministically in tests.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 1,
        half_open_max_calls: int = 1,
        time_func: Callable[[], float] = time.monotonic,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout < 0:
            raise ValueError("recovery_timeout must be >= 0")
        if success_threshold < 1:
            raise ValueError("success_threshold must be >= 1")
        if half_open_max_calls < 1:
            raise ValueError("half_open_max_calls must be >= 1")

        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.half_open_max_calls = half_open_max_calls
        self._now = time_func

        self._lock = threading.RLock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._opened_at: Optional[float] = None

    @property
    def state(self) -> CircuitState:
        """Current state, accounting for any pending recovery transition."""
        with self._lock:
            self._maybe_recover()
            return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failure_count

    def check(self) -> None:
        """Gate a pending call.

        Raises :class:`CircuitBreakerOpenError` when the call must not proceed.
        When the breaker is half-open this also reserves one of the limited
        trial slots, so every successful ``check`` must be paired with exactly
        one :meth:`record_success` or :meth:`record_failure`.
        """
        with self._lock:
            self._maybe_recover()

            if self._state is CircuitState.OPEN:
                raise CircuitBreakerOpenError(self._retry_after())

            if self._state is CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(self._retry_after())
                self._half_open_calls += 1

    def record_success(self) -> None:
        """Report that a gated call succeeded."""
        with self._lock:
            if self._state is CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._reset()
            else:
                self._failure_count = 0

    def record_failure(self) -> None:
        """Report that a gated call failed."""
        with self._lock:
            if self._state is CircuitState.HALF_OPEN:
                # A single failure during recovery means the dependency is
                # still unhealthy; trip immediately.
                self._trip()
                return

            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._trip()

    def reset(self) -> None:
        """Force the breaker back to the healthy closed state."""
        with self._lock:
            self._reset()

    # -- internal helpers (assume the lock is held) ------------------------

    def _maybe_recover(self) -> None:
        if self._state is CircuitState.OPEN and self._opened_at is not None:
            if self._now() - self._opened_at >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                self._success_count = 0
                logger.debug("circuit breaker entering half-open state")

    def _retry_after(self) -> Optional[float]:
        if self._opened_at is None:
            return None
        remaining = self.recovery_timeout - (self._now() - self._opened_at)
        return max(0.0, remaining)

    def _trip(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = self._now()
        self._half_open_calls = 0
        self._success_count = 0
        logger.warning(
            "circuit breaker tripped open after %d failure(s)",
            self._failure_count,
        )

    def _reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._opened_at = None


class ResilientCaller:
    """Executes callables with retry-with-backoff and circuit breaking.

    Only exceptions listed in ``retryable_exceptions`` are retried and counted
    against the circuit breaker. Any other exception is treated as a genuine
    (non-transient) error: it is neither retried nor recorded as a breaker
    failure, and propagates to the caller unchanged.
    """

    def __init__(
        self,
        policy: Optional[BackoffPolicy] = None,
        breaker: Optional[CircuitBreaker] = None,
        retryable_exceptions: Tuple[Type[BaseException], ...] = (Exception,),
        sleep_func: Callable[[float], None] = time.sleep,
        rng: Optional[random.Random] = None,
    ) -> None:
        if not retryable_exceptions:
            raise ValueError("retryable_exceptions must not be empty")

        self.policy = policy or BackoffPolicy()
        self.breaker = breaker or CircuitBreaker()
        self.retryable_exceptions = retryable_exceptions
        self._sleep = sleep_func
        self._rng = rng

    def call(self, func: Callable[..., T], *args: object, **kwargs: object) -> T:
        """Invoke ``func(*args, **kwargs)`` with retries and circuit breaking.

        Returns the function's result on success. Raises
        :class:`CircuitBreakerOpenError` if the breaker rejects the call, or
        :class:`MaxRetriesExceededError` if every attempt fails.
        """
        last_exc: Optional[BaseException] = None

        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                self.breaker.check()
            except CircuitBreakerOpenError:
                if last_exc is not None:
                    # The breaker tripped during this call. Surface the real
                    # cause rather than a bare "circuit open" error.
                    raise MaxRetriesExceededError(attempt - 1, last_exc) from last_exc
                raise

            try:
                result = func(*args, **kwargs)
            except self.retryable_exceptions as exc:
                last_exc = exc
                self.breaker.record_failure()

                if attempt < self.policy.max_attempts:
                    delay = self.policy.compute_delay(attempt, self._rng)
                    logger.warning(
                        "attempt %d/%d failed (%r); retrying in %.2fs",
                        attempt,
                        self.policy.max_attempts,
                        exc,
                        delay,
                    )
                    self._sleep(delay)
                    continue

                raise MaxRetriesExceededError(attempt, exc) from exc
            else:
                self.breaker.record_success()
                return result

        # Unreachable: the loop either returns or raises on every path.
        raise AssertionError("retry loop exited without returning or raising")


def resilient(
    policy: Optional[BackoffPolicy] = None,
    breaker: Optional[CircuitBreaker] = None,
    retryable_exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    sleep_func: Callable[[float], None] = time.sleep,
    rng: Optional[random.Random] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator form of :class:`ResilientCaller`.

    A single :class:`ResilientCaller` (and therefore one circuit breaker) is
    shared across all invocations of the decorated function, so failure state
    persists between calls as intended.
    """

    caller = ResilientCaller(
        policy=policy,
        breaker=breaker,
        retryable_exceptions=retryable_exceptions,
        sleep_func=sleep_func,
        rng=rng,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            return caller.call(func, *args, **kwargs)

        wrapper.resilient_caller = caller  # type: ignore[attr-defined]
        return wrapper

    return decorator


__all__ = [
    "BackoffPolicy",
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerOpenError",
    "MaxRetriesExceededError",
    "ResilienceError",
    "ResilientCaller",
    "resilient",
]
