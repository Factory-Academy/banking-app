"""Fraud detection service orchestration.

Combines the individual rules into a single risk assessment. Rule evaluation is
isolated so that an unexpected failure in one rule degrades gracefully (that
rule contributes no points) instead of aborting the entire assessment.
"""
import logging
from typing import Any, Dict, List

from app.models.transaction import Transaction

from .rules import (
    AmountDeviationRule,
    FirstInternationalRule,
    FraudRule,
    GeographicAnomalyRule,
    HighAmountRule,
    UnusualTimeRule,
    VelocityRule,
)
from .scoring import classify_risk
from .windows import iter_history

logger = logging.getLogger(__name__)


class FraudDetectionService:
    """Service for detecting fraudulent transactions"""

    def __init__(self):
        self.rules: List[FraudRule] = [
            HighAmountRule(),
            VelocityRule(),
            GeographicAnomalyRule(),
            UnusualTimeRule(),
            FirstInternationalRule(),
            AmountDeviationRule(),
        ]

    def analyze_transaction(
        self,
        transaction: Transaction,
        account_history: List[Transaction],
    ) -> Dict[str, Any]:
        """Analyze a transaction and return its risk assessment.

        Returns a dict with ``risk_score``, ``risk_level``, ``status``, and
        ``fraud_flags``. The history is materialised once so each rule scans the
        same stable sequence.
        """
        history = list(iter_history(account_history))
        total_score = 0
        flags = []

        for rule in self.rules:
            try:
                triggered = rule.evaluate(transaction, history)
            except Exception:
                logger.exception(
                    "Fraud rule %r failed; skipping", getattr(rule, "name", rule)
                )
                continue
            if triggered:
                total_score += rule.risk_points
                flags.append(rule.name)

        risk_level, status = classify_risk(total_score)
        return {
            "risk_score": total_score,
            "risk_level": risk_level,
            "status": status,
            "fraud_flags": flags,
        }

    def clear_caches(self) -> None:
        """Drop any memoised state held by the rules."""
        GeographicAnomalyRule._calculate_distance.cache_clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """Return cache statistics for observability."""
        return {
            "distance_calculation": GeographicAnomalyRule._calculate_distance.cache_info()._asdict()
        }
