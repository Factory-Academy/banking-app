"""Exception types raised by the resilience utilities."""

from __future__ import annotations

from typing import Optional


class ResilienceError(Exception):
    """Base class for errors raised by this package."""


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


__all__ = [
    "ResilienceError",
    "CircuitBreakerOpenError",
    "MaxRetriesExceededError",
]
