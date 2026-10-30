from decimal import Decimal

import pytest

from app.models.transaction import RiskLevel, TransactionStatus
from app.services.fraud.scoring import (
    HIGH_RISK_THRESHOLD,
    MEDIUM_RISK_THRESHOLD,
    average_amount,
    classify_risk,
)


class TestClassifyRisk:
    def test_thresholds(self):
        assert HIGH_RISK_THRESHOLD == 70
        assert MEDIUM_RISK_THRESHOLD == 40

    def test_high_is_held(self):
        assert classify_risk(70) == (RiskLevel.HIGH, TransactionStatus.HELD)
        assert classify_risk(150) == (RiskLevel.HIGH, TransactionStatus.HELD)

    def test_medium_boundary_is_cleared(self):
        assert classify_risk(40) == (RiskLevel.MEDIUM, TransactionStatus.CLEARED)
        assert classify_risk(69) == (RiskLevel.MEDIUM, TransactionStatus.CLEARED)

    def test_low_boundary(self):
        assert classify_risk(39) == (RiskLevel.LOW, TransactionStatus.CLEARED)
        assert classify_risk(0) == (RiskLevel.LOW, TransactionStatus.CLEARED)


class TestAverageAmount:
    def test_empty_is_none(self):
        assert average_amount([]) is None

    def test_all_invalid_is_none(self):
        assert average_amount(["x", None, float("nan")]) is None

    def test_mean_of_valid_values(self):
        assert average_amount([Decimal("10"), Decimal("20")]) == Decimal("15")

    def test_ignores_unparseable_values(self):
        assert average_amount([Decimal("10"), "bad", None, Decimal("20")]) == Decimal("15")

    def test_mixed_sources(self):
        assert average_amount(["100", 200, Decimal("300")]) == Decimal("200")
