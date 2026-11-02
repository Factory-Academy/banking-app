"""Shared helpers for keeping risk scores on a well-defined scale.

Every scoring strategy ends by turning a raw ``float`` aggregate into the
integer score the rest of the system reasons about. Two concerns are common to
all of them and easy to get subtly wrong, so they live here once:

* **Rounding.** ``round`` uses banker's rounding, which makes a half-point score
  depend on the parity of the integer part (``round(12.5) == 12`` but
  ``round(13.5) == 14``). Risk scores are easier to explain with deterministic
  half-up rounding.
* **Clamping.** Scores feed :meth:`~app.domain.fraud.RiskAssessment.classify`,
  which rejects a negative score outright. A single rule carrying negative or
  malformed ``risk_points`` (a future rule, a mis-tuned custom one, a test
  double) could otherwise drive a strategy's aggregate below zero and turn a
  routine ``POST /transactions`` into a 500. Flooring the score at
  :data:`SCORE_FLOOR` keeps a malformed rule from crashing the request path; it
  just stops contributing, which is the safe direction for a fraud signal.
"""

from __future__ import annotations

import math

# Lowest score a strategy may emit. Scores are a magnitude of risk, so the floor
# is zero: "no evidence" rather than "negative evidence".
SCORE_FLOOR = 0


def round_half_up(value: float) -> int:
    """Round ``value`` to the nearest int, rounding a half away from zero.

    ``math.floor(value + 0.5)`` rounds halves toward positive infinity, which is
    the intuitive "round up" for the non-negative scores strategies produce. The
    negative branch is handled symmetrically so the helper is total and callers
    never have to special-case a sign before clamping.
    """
    if not math.isfinite(value):
        raise ValueError(f"cannot round non-finite score {value!r}")
    if value < 0:
        return -math.floor(-value + 0.5)
    return math.floor(value + 0.5)


def clamp_score(value: float) -> int:
    """Round ``value`` and clamp it to the valid score range.

    The result is a non-negative ``int`` (at least :data:`SCORE_FLOOR`). There is
    deliberately no upper cap: additive scoring can legitimately exceed 100 when
    many rules fire, and preserving that magnitude keeps the score explainable to
    an analyst. Only the classification thresholds, not the raw score, are
    bounded, and those live in :mod:`app.domain.fraud`.
    """
    return max(SCORE_FLOOR, round_half_up(value))
