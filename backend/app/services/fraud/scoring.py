"""Pluggable risk-scoring strategies.

A fraud rule produces a :class:`~app.domain.fraud.RuleOutcome` (a name, the
points it is worth, and whether it fired). How those per-rule outcomes are
combined into a single risk score is a policy decision, not a fact about the
rules, so it lives behind the :class:`ScoringStrategy` protocol rather than
being hard-coded into the service.

Two implementations ship today:

* :class:`AdditiveScoringStrategy` - the historical behaviour: sum the points of
  every rule that fired. Simple and explainable, but the score grows without
  bound as more (often correlated) rules trigger.
* :class:`DampenedScoringStrategy` - diminishing returns: the largest signal
  counts in full and each additional signal contributes a decaying fraction.
  This reflects that overlapping fraud signals are correlated, so stacking many
  of them should not blow the score past the thresholds on its own.

Strategies deliberately return a plain ``int`` on the same 0-100ish point scale
the thresholds in :mod:`app.domain.fraud` use. Mapping that score to a risk
level and status stays centralised in
:meth:`~app.domain.fraud.RiskAssessment.from_score`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import ClassVar, Protocol, Sequence, runtime_checkable

from app.domain.fraud import RuleOutcome


@runtime_checkable
class ScoringStrategy(Protocol):
    """Combine per-rule outcomes into a single integer risk score.

    Implementations must expose a ``name`` identifying the policy and a
    :meth:`score` that is a pure function of the outcomes passed to it. Scores
    are non-negative and live on the same point scale as the risk thresholds.
    """

    name: str

    def score(self, outcomes: Sequence[RuleOutcome]) -> int:
        """Return the aggregate risk score for ``outcomes``."""
        ...


def _triggered_points(outcomes: Sequence[RuleOutcome]) -> list[int]:
    """Points of the rules that fired, highest first."""
    return sorted(
        (outcome.risk_points for outcome in outcomes if outcome.triggered),
        reverse=True,
    )


def _round_half_up(value: float) -> int:
    """Round a non-negative value to the nearest int, halves rounding up.

    ``round`` uses banker's rounding, which makes half-point scores depend on
    the parity of the integer part. Risk scores are easier to reason about with
    deterministic half-up rounding.
    """
    return int(math.floor(value + 0.5))


@dataclass(frozen=True)
class AdditiveScoringStrategy:
    """Sum the points of every rule that fired.

    This is the original scoring policy and the default, so swapping the service
    onto the strategy abstraction is behaviour-preserving.
    """

    name: ClassVar[str] = "additive"

    def score(self, outcomes: Sequence[RuleOutcome]) -> int:
        return sum(outcome.awarded_points for outcome in outcomes)


@dataclass(frozen=True)
class DampenedScoringStrategy:
    """Diminishing-returns scoring over the triggered rules.

    Triggered points are ranked highest-first; the top signal counts in full and
    each subsequent signal is multiplied by ``decay ** rank``. With ``decay`` of
    1.0 this reduces exactly to additive scoring; smaller values penalise piling
    on many correlated signals.
    """

    decay: float = 0.5
    name: ClassVar[str] = "dampened"

    def __post_init__(self) -> None:
        if not 0.0 < self.decay <= 1.0:
            raise ValueError(
                f"decay must be in the interval (0, 1], got {self.decay!r}"
            )

    def score(self, outcomes: Sequence[RuleOutcome]) -> int:
        total = 0.0
        for rank, points in enumerate(_triggered_points(outcomes)):
            total += points * (self.decay**rank)
        return _round_half_up(total)
