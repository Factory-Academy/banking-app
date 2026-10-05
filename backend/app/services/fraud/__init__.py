"""Fraud detection package.

Public surface is re-exported here so callers can import from
``app.services.fraud`` while the implementation stays split across small,
single-responsibility modules.
"""

from .rules import (
    AmountDeviationRule,
    FirstInternationalRule,
    FraudRule,
    GeographicAnomalyRule,
    HighAmountRule,
    UnusualTimeRule,
    VelocityRule,
)
from .scoring import (
    HIGH_RISK_THRESHOLD,
    MEDIUM_RISK_THRESHOLD,
    average_amount,
    classify_risk,
)
from .service import FraudDetectionService

__all__ = [
    "FraudDetectionService",
    "FraudRule",
    "HighAmountRule",
    "VelocityRule",
    "GeographicAnomalyRule",
    "UnusualTimeRule",
    "FirstInternationalRule",
    "AmountDeviationRule",
    "classify_risk",
    "average_amount",
    "HIGH_RISK_THRESHOLD",
    "MEDIUM_RISK_THRESHOLD",
]
