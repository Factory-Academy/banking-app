"""Exponential backoff delay computation."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Optional

# Shared source of jitter used when a caller does not supply its own RNG.
_DEFAULT_RNG = random.Random()


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
        failed attempt. The returned value is always a finite, non-negative
        number and never exceeds :attr:`max_delay`.

        Large ``attempt`` values do not raise: exponentiating ``multiplier``
        can overflow to ``inf`` (or raise :class:`OverflowError`), so the raw
        term is computed defensively and any non-finite result falls back to
        :attr:`max_delay` rather than propagating a crash to the retry loop.
        """
        if attempt < 1:
            raise ValueError("attempt must be >= 1")

        if self.base_delay == 0.0:
            # Short-circuit: a zero base delay is always zero, and skipping the
            # multiplication avoids the 0 * inf -> nan trap for huge attempts.
            raw = 0.0
        else:
            try:
                raw = self.base_delay * (self.multiplier ** (attempt - 1))
            except OverflowError:
                raw = math.inf
            if not math.isfinite(raw):
                raw = self.max_delay

        delay = min(raw, self.max_delay)

        if self.jitter:
            source = rng if rng is not None else _DEFAULT_RNG
            delay = source.uniform(0.0, delay)

        return delay


__all__ = ["BackoffPolicy"]
