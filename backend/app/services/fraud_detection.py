"""Backward-compatible facade for the fraud detection package.

The implementation moved into the ``app.services.fraud`` package, split into
small, independently testable modules (normalization, geo, windows, scoring,
rules, service). This module re-exports the public names so existing imports
such as ``from app.services.fraud_detection import FraudDetectionService``
keep working unchanged.
"""

from app.services.fraud import (
    AmountDeviationRule,
    FirstInternationalRule,
    FraudDetectionService,
    FraudRule,
    GeographicAnomalyRule,
    HighAmountRule,
    UnusualTimeRule,
    VelocityRule,
    classify_risk,
)

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
]
