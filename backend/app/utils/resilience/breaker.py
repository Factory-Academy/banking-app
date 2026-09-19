"""A thread-safe circuit breaker."""

from __future__ import annotations

import logging
import threading
import time
from enum import Enum
from typing import Callable, Optional

from .errors import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


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
    - ``HALF_OPEN``: up to ``half_open_max_calls`` trial calls may be in flight
      at once. ``success_threshold`` successes close the breaker; any failure
      reopens it. A trial slot is reserved by :meth:`check` and released when
      the call resolves (via :meth:`record_success`, :meth:`record_failure`, or
      :meth:`release`), so a slot is never permanently consumed by a probe that
      never reports its outcome.

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
        # Number of trial calls currently in flight while half-open.
        self._half_open_inflight = 0
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
        one :meth:`record_success`, :meth:`record_failure`, or :meth:`release`
        to free that slot.
        """
        with self._lock:
            self._maybe_recover()

            if self._state is CircuitState.OPEN:
                raise CircuitBreakerOpenError(self._retry_after())

            if self._state is CircuitState.HALF_OPEN:
                if self._half_open_inflight >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(self._retry_after())
                self._half_open_inflight += 1

    def record_success(self) -> None:
        """Report that a gated call succeeded."""
        with self._lock:
            if self._state is CircuitState.HALF_OPEN:
                self._release_slot()
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
                # still unhealthy; trip immediately (which clears the slots).
                self._trip()
                return

            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._trip()

    def release(self) -> None:
        """Release a half-open trial slot reserved by :meth:`check`.

        Use this when a gated call finishes without a recorded success or
        failure (for example a non-transient exception that is deliberately
        not counted against the breaker). It is a no-op outside the half-open
        state, so it is always safe to call.
        """
        with self._lock:
            if self._state is CircuitState.HALF_OPEN:
                self._release_slot()

    def reset(self) -> None:
        """Force the breaker back to the healthy closed state."""
        with self._lock:
            self._reset()

    # -- internal helpers (assume the lock is held) ------------------------

    def _maybe_recover(self) -> None:
        if self._state is CircuitState.OPEN and self._opened_at is not None:
            if self._now() - self._opened_at >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._half_open_inflight = 0
                self._success_count = 0
                logger.debug("circuit breaker entering half-open state")

    def _retry_after(self) -> Optional[float]:
        if self._opened_at is None:
            return None
        remaining = self.recovery_timeout - (self._now() - self._opened_at)
        return max(0.0, remaining)

    def _release_slot(self) -> None:
        if self._half_open_inflight > 0:
            self._half_open_inflight -= 1

    def _trip(self) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = self._now()
        self._half_open_inflight = 0
        self._success_count = 0
        logger.warning(
            "circuit breaker tripped open after %d failure(s)",
            self._failure_count,
        )

    def _reset(self) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_inflight = 0
        self._opened_at = None


__all__ = ["CircuitState", "CircuitBreaker"]
