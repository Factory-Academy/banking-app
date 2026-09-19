"""Combine retry-with-backoff and circuit breaking behind one call site."""

from __future__ import annotations

import functools
import logging
import random
import time
from typing import Callable, Optional, Tuple, Type, TypeVar

from .backoff import BackoffPolicy
from .breaker import CircuitBreaker
from .errors import CircuitBreakerOpenError, MaxRetriesExceededError

logger = logging.getLogger(__name__)

T = TypeVar("T")


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

            # check() may have reserved a half-open trial slot. Guarantee that
            # slot is freed even if func raises a non-retryable (unrecorded)
            # exception, otherwise recovery probing is starved permanently.
            outcome_recorded = False
            try:
                result = func(*args, **kwargs)
            except self.retryable_exceptions as exc:
                last_exc = exc
                self.breaker.record_failure()
                outcome_recorded = True

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
                outcome_recorded = True
                return result
            finally:
                if not outcome_recorded:
                    self.breaker.release()

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


__all__ = ["ResilientCaller", "resilient"]
