"""Fraud-scoring strategy package: a pluggable policy behind a factory."""

from app.services.fraud.factory import (
    DEFAULT_STRATEGY,
    available_strategies,
    create_scoring_strategy,
    register_scoring_strategy,
)
from app.services.fraud.scoring import (
    AdditiveScoringStrategy,
    DampenedScoringStrategy,
    ScoringStrategy,
)

__all__ = [
    "ScoringStrategy",
    "AdditiveScoringStrategy",
    "DampenedScoringStrategy",
    "create_scoring_strategy",
    "available_strategies",
    "register_scoring_strategy",
    "DEFAULT_STRATEGY",
]
