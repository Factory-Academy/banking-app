"""Factory and registry for scoring strategies.

Callers name the policy they want (``"additive"``, ``"dampened"``) and pass any
construction arguments through; they never import the concrete classes. This
keeps the choice of policy at the edges (config, a request parameter, a test)
and makes new strategies discoverable through :func:`available_strategies`.
"""

from __future__ import annotations

from typing import Callable, Dict, List

from app.services.fraud.scoring import (
    AdditiveScoringStrategy,
    DampenedScoringStrategy,
    ScoringStrategy,
)

# Maps a strategy name to a callable that builds it. Values are the strategy
# classes themselves today, but any ``(**kwargs) -> ScoringStrategy`` callable
# works, which is what lets third parties register their own.
StrategyBuilder = Callable[..., ScoringStrategy]

_REGISTRY: Dict[str, StrategyBuilder] = {
    AdditiveScoringStrategy.name: AdditiveScoringStrategy,
    DampenedScoringStrategy.name: DampenedScoringStrategy,
}

DEFAULT_STRATEGY = AdditiveScoringStrategy.name


def available_strategies() -> List[str]:
    """Return the registered strategy names, sorted for stable display."""
    return sorted(_REGISTRY)


def create_scoring_strategy(
    name: str = DEFAULT_STRATEGY, **kwargs: object
) -> ScoringStrategy:
    """Build a scoring strategy by name.

    Extra keyword arguments are forwarded to the strategy's constructor, e.g.
    ``create_scoring_strategy("dampened", decay=0.3)``. Raises ``ValueError`` for
    an unknown name so misconfiguration fails loudly rather than silently
    falling back to a default.
    """
    try:
        builder = _REGISTRY[name]
    except KeyError:
        raise ValueError(
            f"Unknown scoring strategy {name!r}. "
            f"Available: {available_strategies()}"
        ) from None
    return builder(**kwargs)


def register_scoring_strategy(name: str, builder: StrategyBuilder) -> None:
    """Register a new strategy builder under ``name``.

    Intended for extension and tests. Rejects names that are already taken so a
    typo cannot silently shadow a built-in policy.
    """
    if name in _REGISTRY:
        raise ValueError(f"Scoring strategy {name!r} is already registered")
    _REGISTRY[name] = builder
