"""Retry-with-backoff and circuit-breaker utilities.

Small, dependency-free building blocks for making outbound calls (HTTP
clients, database drivers, third-party SDKs) tolerant of transient failures:

- :class:`BackoffPolicy` computes exponential backoff delays with optional
  full jitter.
- :class:`CircuitBreaker` trips open after repeated failures so a struggling
  dependency is given time to recover instead of being hammered.
- :class:`ResilientCaller` combines the two behind a single ``call`` method,
  and :func:`resilient` exposes the same behavior as a decorator.

The package relies only on the standard library. Time and randomness are
injectable (``time_func``, ``sleep_func``, ``rng``) so behavior is fully
deterministic under test.

The implementation is split across focused submodules (:mod:`errors`,
:mod:`backoff`, :mod:`breaker`, :mod:`caller`), but the public API is
re-exported here so ``from app.utils.resilience import ...`` keeps working.
"""

from __future__ import annotations

from .backoff import BackoffPolicy
from .breaker import CircuitBreaker, CircuitState
from .caller import ResilientCaller, resilient
from .errors import (
    CircuitBreakerOpenError,
    MaxRetriesExceededError,
    ResilienceError,
)

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
