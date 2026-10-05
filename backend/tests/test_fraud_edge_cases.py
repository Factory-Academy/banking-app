"""Regression suite for a class of edge-case bugs in the fraud path.

Covers malformed field values, empty history, large history, and fault
isolation between rules. These guard the behaviour added when the monolithic
``analyze_transaction`` helper was split into small pure functions.
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models.transaction import RiskLevel, Transaction, TransactionStatus
from app.services.fraud_detection import (
    AmountDeviationRule,
    FraudDetectionService,
    FraudRule,
    GeographicAnomalyRule,
    HighAmountRule,
    UnusualTimeRule,
    VelocityRule,
)


def make_txn(**overrides) -> Transaction:
    base = dict(
        id="TXN-EDGE",
        account_number="**** 4521",
        account_holder_name="John Smith",
        amount=Decimal("500.00"),
        merchant_name="Test Merchant",
        merchant_category="Retail",
        transaction_type="CARD",
        location_city="New York",
        location_country="US",
        latitude=40.7128,
        longitude=-74.0060,
        timestamp=datetime(2024, 6, 1, 12, 0, 0),
        status=TransactionStatus.CLEARED,
        risk_level=RiskLevel.LOW,
        risk_score=0,
        fraud_flags=[],
    )
    base.update(overrides)
    return Transaction(**base)


@pytest.fixture
def fraud_service():
    return FraudDetectionService()


class TestMalformedAmount:
    def test_high_amount_rule_handles_none_amount(self):
        assert HighAmountRule().evaluate(make_txn(amount=None), []) is False

    def test_amount_deviation_handles_malformed_current_amount(self):
        history = [make_txn(amount=Decimal("300.00")) for _ in range(5)]
        assert AmountDeviationRule().evaluate(make_txn(amount="oops"), history) is False

    def test_amount_deviation_skips_malformed_history_entries(self):
        # Three valid entries averaging 300 plus junk entries; 3000 > 3x300.
        history = [
            make_txn(amount=Decimal("300.00")),
            make_txn(amount=None),
            make_txn(amount=Decimal("300.00")),
            make_txn(amount="junk"),
            make_txn(amount=Decimal("300.00")),
        ]
        assert AmountDeviationRule().evaluate(make_txn(amount=Decimal("3000.00")), history) is True

    def test_amount_deviation_requires_three_valid_entries(self):
        history = [make_txn(amount=Decimal("300.00")), make_txn(amount=None)]
        assert AmountDeviationRule().evaluate(make_txn(amount=Decimal("3000.00")), history) is False

    def test_service_does_not_crash_on_malformed_amount(self, fraud_service):
        result = fraud_service.analyze_transaction(make_txn(amount=None), [])
        assert result["risk_level"] == RiskLevel.LOW
        assert "high_amount" not in result["fraud_flags"]


class TestMissingTimestamp:
    def test_velocity_rule_handles_missing_timestamp(self):
        history = [make_txn() for _ in range(6)]
        assert VelocityRule().evaluate(make_txn(timestamp=None), history) is False

    def test_unusual_time_rule_handles_missing_timestamp(self):
        assert UnusualTimeRule().evaluate(make_txn(timestamp=None), []) is False

    def test_geo_rule_handles_missing_timestamp(self):
        prev = make_txn(location_country="CN", timestamp=datetime(2024, 6, 1, 10, 0, 0))
        assert GeographicAnomalyRule().evaluate(make_txn(timestamp=None), [prev]) is False

    def test_velocity_skips_history_entries_without_timestamp(self):
        now = datetime(2024, 6, 1, 12, 0, 0)
        history = [make_txn(timestamp=now - timedelta(minutes=5 * i)) for i in range(6)]
        history += [make_txn(timestamp=None) for _ in range(3)]
        assert VelocityRule().evaluate(make_txn(timestamp=now), history) is True


class TestZeroCoordinates:
    def test_geo_rule_uses_zero_coordinates(self):
        # Regression: a prior transaction at (0, 0) must not be treated as
        # "no coordinates". It is ~8,600 km from New York, so the cross-border
        # move should flag.
        prev = make_txn(
            location_country="GH",
            latitude=0.0,
            longitude=0.0,
            timestamp=datetime(2024, 6, 1, 11, 0, 0),
        )
        current = make_txn(
            location_country="US",
            latitude=40.7128,
            longitude=-74.0060,
            timestamp=datetime(2024, 6, 1, 12, 0, 0),
        )
        assert GeographicAnomalyRule().evaluate(current, [prev]) is True

    def test_geo_rule_missing_coords_flags_on_country_difference(self):
        prev = make_txn(
            location_country="CN",
            latitude=None,
            longitude=None,
            timestamp=datetime(2024, 6, 1, 11, 0, 0),
        )
        current = make_txn(
            location_country="US",
            latitude=None,
            longitude=None,
            timestamp=datetime(2024, 6, 1, 12, 0, 0),
        )
        assert GeographicAnomalyRule().evaluate(current, [prev]) is True


class TestEmptyAndNoneHistory:
    def test_empty_history_is_low_risk(self, fraud_service):
        result = fraud_service.analyze_transaction(make_txn(), [])
        assert result["risk_level"] == RiskLevel.LOW
        assert result["fraud_flags"] == []

    def test_none_history_is_handled(self, fraud_service):
        result = fraud_service.analyze_transaction(make_txn(), None)
        assert result["risk_score"] == 0


class TestLargeHistory:
    def test_large_history_velocity_flags(self, fraud_service):
        now = datetime(2024, 6, 1, 12, 0, 0)
        # 2,000 old transactions plus 6 within the last hour.
        history = [make_txn(timestamp=now - timedelta(days=i + 1)) for i in range(2000)]
        history += [make_txn(timestamp=now - timedelta(minutes=5 * i)) for i in range(6)]
        result = fraud_service.analyze_transaction(make_txn(timestamp=now), history)
        assert "high_velocity" in result["fraud_flags"]

    def test_large_history_does_not_error(self, fraud_service):
        now = datetime(2024, 6, 1, 12, 0, 0)
        history = [make_txn(timestamp=now - timedelta(hours=i + 1)) for i in range(5000)]
        result = fraud_service.analyze_transaction(make_txn(timestamp=now), history)
        assert isinstance(result["risk_score"], int)


class TestRuleFaultIsolation:
    def test_failing_rule_does_not_abort_analysis(self, fraud_service):
        class ExplodingRule(FraudRule):
            def __init__(self):
                super().__init__("exploding", 10)

            def evaluate(self, transaction, account_history):
                raise RuntimeError("boom")

        fraud_service.rules.insert(0, ExplodingRule())
        result = fraud_service.analyze_transaction(make_txn(), [])
        # The remaining rules still run; the exploding rule contributes nothing.
        assert "exploding" not in result["fraud_flags"]
        assert result["risk_level"] == RiskLevel.LOW
