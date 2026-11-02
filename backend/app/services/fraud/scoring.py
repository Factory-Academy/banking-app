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
the thresholds in :mod:`app.domain.fraud` use, clamped non-negative (see
:mod:`app.services.fraud.bounds`) so a malformed rule cannot produce a score
that :meth:`~app.domain.fraud.RiskAssessment.classify` would reject. Mapping that
score to a risk level and status stays centralised in
:meth:`~app.domain.fraud.RiskAssessment.from_score`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Protocol, Sequence, runtime_checkable

from app.domain.fraud import RuleOutcome
from app.services.fraud.bounds import clamp_score


@runtime_checkable
class ScoringStrategy(Protocol):
    """Combine per-rule outcomes into a single integer risk score.

    Implementations must expose a ``name`` identifying the policy and a
    :meth:`score` that is a pure function of the outcomes passed to it. Scores
    are non-negative and live on the same point scale as the risk thresholds;
    implementations guarantee that by funnelling their aggregate through
    :func:`~app.services.fraud.bounds.clamp_score`.
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


@dataclass(frozen=True)
class AdditiveScoringStrategy:
    """Sum the points of every rule that fired.

    This is the original scoring policy and the default, so swapping the service
    onto the strategy abstraction is behaviour-preserving.
    """

    name: ClassVar[str] = "additive"

    def score(self, outcomes: Sequence[RuleOutcome]) -> int:
        total = sum(outcome.awarded_points for outcome in outcomes)
        return clamp_score(total)


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
        return clamp_score(total)
