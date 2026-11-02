"""Factory and registry for scoring strategies.

Callers name the policy they want (``"additive"``, ``"dampened"``) and pass any
construction arguments through; they never import the concrete classes. This
keeps the choice of policy at the edges (config, a request parameter, a test)
and makes new strategies discoverable through :func:`available_strategies`.

Extensions and tests add and remove strategies through the public
:func:`register_scoring_strategy` / :func:`unregister_scoring_strategy` pair (or
the :func:`temporary_strategy` context manager) rather than touching the private
registry, so cleanup is reliable and the built-in policies cannot be clobbered.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Dict, Iterator, List

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

# The strategies that ship with the package. They are protected from
# unregistration so a test or extension cannot leave the registry missing a
# policy the live service depends on.
_BUILTIN_STRATEGIES = frozenset(_REGISTRY)

DEFAULT_STRATEGY = AdditiveScoringStrategy.name


def _normalize_name(name: str) -> str:
    """Validate and canonicalise a strategy name.

    Names are used as registry keys, surfaced by :func:`available_strategies`,
    and typically come from config or a request, so a blank or non-string name
    is a programming/config error worth rejecting at the boundary rather than
    storing an unreachable key. Surrounding whitespace is stripped so
    ``"dampened "`` and ``"dampened"`` cannot register as two policies.
    """
    if not isinstance(name, str):
        raise TypeError(f"strategy name must be a str, got {type(name).__name__}")
    normalized = name.strip()
    if not normalized:
        raise ValueError("strategy name must be a non-empty string")
    return normalized


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
    key = _normalize_name(name)
    try:
        builder = _REGISTRY[key]
    except KeyError:
        raise ValueError(
            f"Unknown scoring strategy {key!r}. "
            f"Available: {available_strategies()}"
        ) from None
    return builder(**kwargs)


def register_scoring_strategy(name: str, builder: StrategyBuilder) -> None:
    """Register a new strategy builder under ``name``.

    Intended for extension and tests. Rejects blank names and names that are
    already taken so a typo cannot silently shadow a built-in policy. Pair with
    :func:`unregister_scoring_strategy` (or use :func:`temporary_strategy`) to
    clean up.
    """
    key = _normalize_name(name)
    if not callable(builder):
        raise TypeError("builder must be callable")
    if key in _REGISTRY:
        raise ValueError(f"Scoring strategy {key!r} is already registered")
    _REGISTRY[key] = builder


def unregister_scoring_strategy(name: str) -> None:
    """Remove a previously registered strategy.

    Raises ``ValueError`` for a built-in policy (which must stay available for
    the live service) and ``KeyError`` for a name that was never registered, so
    a buggy cleanup surfaces instead of passing silently.
    """
    key = _normalize_name(name)
    if key in _BUILTIN_STRATEGIES:
        raise ValueError(f"Cannot unregister built-in strategy {key!r}")
    del _REGISTRY[key]


@contextmanager
def temporary_strategy(name: str, builder: StrategyBuilder) -> Iterator[str]:
    """Register ``builder`` for the duration of the ``with`` block.

    A convenience for tests and short-lived extensions: the strategy is
    registered on entry and unregistered on exit even if the body raises, so the
    global registry is always restored. Yields the normalised name.
    """
    key = _normalize_name(name)
    register_scoring_strategy(key, builder)
    try:
        yield key
    finally:
        unregister_scoring_strategy(key)
