"""Regression suite for the defensive behaviour of the fraud rule layer.

These cover the class of edge-case bugs the refactor targets: empty, malformed,
and large inputs must never raise, and must not silently misfire the way the
original truthiness/None-unsafe implementation did.
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.models.transaction import RiskLevel, Transaction, TransactionStatus
from app.services.fraud import FraudDetectionService
from app.services.fraud.rules import (
    AmountDeviationRule,
    FirstInternationalRule,
    GeographicAnomalyRule,
    HighAmountRule,
    UnusualTimeRule,
    VelocityRule,
)

REF = datetime(2025, 1, 1, 12, 0)


def make_txn(**overrides) -> Transaction:
    base = dict(
        id="TXN-TEST",
        account_number="**** 4521",
        account_holder_name="John Smith",
        amount=Decimal("100.00"),
        merchant_name="Test Merchant",
        merchant_category="Retail",
        transaction_type="CARD",
        location_city="New York",
        location_country="US",
        latitude=40.7128,
        longitude=-74.0060,
        timestamp=REF,
        status=TransactionStatus.CLEARED,
        risk_level=RiskLevel.LOW,
        risk_score=0,
        fraud_flags=[],
    )
    base.update(overrides)
    return Transaction(**base)


ALL_RULE_CLASSES = [
    HighAmountRule,
    VelocityRule,
    GeographicAnomalyRule,
    UnusualTimeRule,
    FirstInternationalRule,
    AmountDeviationRule,
]


@pytest.fixture
def service():
    return FraudDetectionService()


class TestRulesNeverRaise:
    @pytest.mark.parametrize("rule_cls", ALL_RULE_CLASSES)
    def test_bare_transaction_with_no_attributes(self, rule_cls):
        bare = Transaction()
        result = rule_cls().evaluate(bare, [])
        assert result in (True, False)

    @pytest.mark.parametrize("rule_cls", ALL_RULE_CLASSES)
    def test_null_fields(self, rule_cls):
        txn = make_txn(amount=None, timestamp=None, location_country=None,
                       latitude=None, longitude=None)
        assert rule_cls().evaluate(txn, []) in (True, False)

    @pytest.mark.parametrize("rule_cls", ALL_RULE_CLASSES)
    def test_malformed_fields(self, rule_cls):
        txn = make_txn(amount="oops", timestamp="yesterday", location_country=123,
                       latitude="north", longitude=object())
        assert rule_cls().evaluate(txn, []) in (True, False)

    @pytest.mark.parametrize("rule_cls", ALL_RULE_CLASSES)
    def test_history_with_bad_rows(self, rule_cls):
        history = [
            Transaction(),
            make_txn(amount="bad", timestamp="bad"),
            make_txn(timestamp=None),
        ]
        assert rule_cls().evaluate(make_txn(), history) in (True, False)


class TestHighAmountEdgeCases:
    def test_malformed_amount_does_not_fire(self):
        assert HighAmountRule().evaluate(make_txn(amount="NaN"), []) is False

    def test_boundary(self):
        assert HighAmountRule().evaluate(make_txn(amount=Decimal("10000")), []) is False
        assert HighAmountRule().evaluate(make_txn(amount=Decimal("10000.01")), []) is True


class TestGeographicEdgeCases:
    def test_zero_coordinates_are_respected(self):
        # Equator transaction followed by a far one: 0.0 must not read as missing.
        prev = make_txn(timestamp=REF - timedelta(hours=1), location_country="BR",
                        latitude=0.0, longitude=0.0)
        cur = make_txn(timestamp=REF, location_country="JP",
                       latitude=35.0, longitude=139.0)
        assert GeographicAnomalyRule().evaluate(cur, [prev]) is True

    def test_country_change_without_coordinates_still_flags(self):
        prev = make_txn(timestamp=REF - timedelta(hours=1), location_country="US",
                        latitude=None, longitude=None)
        cur = make_txn(timestamp=REF, location_country="CN",
                       latitude=None, longitude=None)
        assert GeographicAnomalyRule().evaluate(cur, [prev]) is True

    def test_same_country_does_not_flag(self):
        prev = make_txn(timestamp=REF - timedelta(hours=1), location_country="US")
        cur = make_txn(timestamp=REF, location_country="US")
        assert GeographicAnomalyRule().evaluate(cur, [prev]) is False

    def test_outside_window_ignored(self):
        prev = make_txn(timestamp=REF - timedelta(hours=6), location_country="CN",
                        latitude=22.3, longitude=114.1)
        cur = make_txn(timestamp=REF, location_country="US")
        assert GeographicAnomalyRule().evaluate(cur, [prev]) is False


class TestAmountDeviationEdgeCases:
    def test_zero_average_does_not_divide_by_zero(self):
        history = [make_txn(amount=Decimal("0")) for _ in range(5)]
        assert AmountDeviationRule().evaluate(make_txn(amount=Decimal("500")), history) is False

    def test_history_of_malformed_amounts_is_insufficient(self):
        history = [make_txn(amount="bad") for _ in range(5)]
        assert AmountDeviationRule().evaluate(make_txn(amount=Decimal("5000")), history) is False

    def test_mixed_valid_and_invalid_history(self):
        history = [make_txn(amount=Decimal("300")) for _ in range(5)]
        history += [make_txn(amount=None), make_txn(amount="bad")]
        assert AmountDeviationRule().evaluate(make_txn(amount=Decimal("3000")), history) is True


class TestServiceResilience:
    def test_empty_history(self, service):
        result = service.analyze_transaction(make_txn(timestamp=REF.replace(hour=12)), [])
        assert isinstance(result["risk_score"], int)
        assert result["risk_level"] == RiskLevel.LOW

    def test_none_history(self, service):
        result = service.analyze_transaction(make_txn(timestamp=REF.replace(hour=12)), None)
        assert result["risk_level"] == RiskLevel.LOW

    def test_large_history_is_handled(self, service):
        # A big history must not raise and must complete.
        history = [
            make_txn(id=f"TXN-{i}", timestamp=REF - timedelta(days=i % 30, minutes=i))
            for i in range(5000)
        ]
        result = service.analyze_transaction(make_txn(timestamp=REF.replace(hour=12)), history)
        assert isinstance(result["risk_score"], int)

    def test_history_with_malformed_rows(self, service):
        history = [Transaction(), make_txn(amount="bad", timestamp="bad"), make_txn()]
        result = service.analyze_transaction(make_txn(timestamp=REF.replace(hour=12)), history)
        assert isinstance(result["fraud_flags"], list)

    def test_high_risk_still_held(self, service):
        txn = make_txn(amount=Decimal("15000"), location_country="CN",
                       timestamp=REF.replace(hour=3))
        result = service.analyze_transaction(txn, [])
        assert result["status"] == TransactionStatus.HELD
        assert result["risk_score"] >= 70

    def test_failing_rule_is_isolated(self, service):
        class Boom(HighAmountRule):
            def evaluate(self, transaction, account_history):
                raise RuntimeError("boom")

        service.rules = [Boom(), UnusualTimeRule()]
        # The failing rule contributes nothing; the assessment still completes.
        result = service.analyze_transaction(make_txn(timestamp=REF.replace(hour=12)), [])
        assert result["risk_score"] == 0
        assert result["fraud_flags"] == []


class TestDistanceCache:
    def test_cache_clear_and_info(self, service):
        service.clear_caches()
        prev = make_txn(timestamp=REF - timedelta(hours=1), location_country="CN",
                        latitude=22.3, longitude=114.1)
        cur = make_txn(timestamp=REF, location_country="US")
        GeographicAnomalyRule().evaluate(cur, [prev])
        info = service.get_cache_info()
        assert "distance_calculation" in info
        assert info["distance_calculation"]["currsize"] >= 1
        service.clear_caches()
        assert service.get_cache_info()["distance_calculation"]["currsize"] == 0
