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
    def test_high_at_and_above_threshold(self):
        assert classify_risk(HIGH_RISK_THRESHOLD) == (RiskLevel.HIGH, TransactionStatus.HELD)
        assert classify_risk(100) == (RiskLevel.HIGH, TransactionStatus.HELD)

    def test_medium_band(self):
        assert classify_risk(MEDIUM_RISK_THRESHOLD) == (RiskLevel.MEDIUM, TransactionStatus.CLEARED)
        assert classify_risk(HIGH_RISK_THRESHOLD - 1) == (RiskLevel.MEDIUM, TransactionStatus.CLEARED)

    def test_low_band(self):
        assert classify_risk(0) == (RiskLevel.LOW, TransactionStatus.CLEARED)
        assert classify_risk(MEDIUM_RISK_THRESHOLD - 1) == (RiskLevel.LOW, TransactionStatus.CLEARED)

    def test_boundaries_are_inclusive_lower_bound(self):
        # Exactly 39 -> LOW, exactly 40 -> MEDIUM, exactly 69 -> MEDIUM, 70 -> HIGH.
        assert classify_risk(39)[0] == RiskLevel.LOW
        assert classify_risk(40)[0] == RiskLevel.MEDIUM
        assert classify_risk(69)[0] == RiskLevel.MEDIUM
        assert classify_risk(70)[0] == RiskLevel.HIGH


class TestAverageAmount:
    def test_simple_average(self):
        assert average_amount([Decimal("100"), Decimal("200"), Decimal("300")]) == Decimal("200")

    def test_empty_returns_none(self):
        assert average_amount([]) is None

    def test_skips_malformed_values(self):
        # None / non-numeric entries are ignored, not fatal.
        assert average_amount([Decimal("100"), None, "oops", Decimal("300")]) == Decimal("200")

    def test_all_malformed_returns_none(self):
        assert average_amount([None, "bad", float("nan")]) is None
