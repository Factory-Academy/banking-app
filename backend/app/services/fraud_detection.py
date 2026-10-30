"""Backward-compatible entry point for the fraud detection service.

The implementation now lives in the :mod:`app.services.fraud` package, split
into small, individually testable modules (coercion, geo, time windows,
scoring, rules, and orchestration). This module re-exports the public surface so
existing imports and the API layer keep working unchanged.
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
]
