import dataclasses
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.domain.fraud import (
    HIGH_RISK_THRESHOLD,
    MEDIUM_RISK_THRESHOLD,
    RiskAssessment,
    RuleOutcome,
)
from app.domain.seeding import TransactionDraft
from app.domain.stats import DashboardStats, RiskBreakdown
from app.models.transaction import RiskLevel, TransactionStatus


class TestRuleOutcome:
    def test_awarded_points_when_triggered(self):
        outcome = RuleOutcome(name="high_amount", risk_points=30, triggered=True)
        assert outcome.awarded_points == 30

    def test_awarded_points_when_not_triggered(self):
        outcome = RuleOutcome(name="high_amount", risk_points=30, triggered=False)
        assert outcome.awarded_points == 0

    def test_is_immutable(self):
        outcome = RuleOutcome(name="high_amount", risk_points=30, triggered=True)
        with pytest.raises(dataclasses.FrozenInstanceError):
            outcome.triggered = False  # type: ignore[misc]


class TestRiskAssessmentClassify:
    def test_low_below_medium_threshold(self):
        assert RiskAssessment.classify(MEDIUM_RISK_THRESHOLD - 1) == (
            RiskLevel.LOW,
            TransactionStatus.CLEARED,
        )

    def test_zero_is_low(self):
        assert RiskAssessment.classify(0) == (RiskLevel.LOW, TransactionStatus.CLEARED)

    def test_medium_at_exact_threshold(self):
        assert RiskAssessment.classify(MEDIUM_RISK_THRESHOLD) == (
            RiskLevel.MEDIUM,
            TransactionStatus.CLEARED,
        )

    def test_medium_just_below_high(self):
        assert RiskAssessment.classify(HIGH_RISK_THRESHOLD - 1) == (
            RiskLevel.MEDIUM,
            TransactionStatus.CLEARED,
        )

    def test_high_at_exact_threshold_is_held(self):
        assert RiskAssessment.classify(HIGH_RISK_THRESHOLD) == (
            RiskLevel.HIGH,
            TransactionStatus.HELD,
        )

    def test_negative_score_raises(self):
        with pytest.raises(ValueError):
            RiskAssessment.classify(-1)


class TestRiskAssessmentFromScore:
    def test_builds_low_assessment(self):
        assessment = RiskAssessment.from_score(10, ["unusual_time"])
        assert assessment.risk_score == 10
        assert assessment.risk_level == RiskLevel.LOW
        assert assessment.status == TransactionStatus.CLEARED
        assert assessment.fraud_flags == ["unusual_time"]
        assert assessment.is_held is False

    def test_high_assessment_is_held(self):
        assessment = RiskAssessment.from_score(80, ["high_amount"])
        assert assessment.is_held is True

    def test_defaults_to_empty_flags(self):
        assessment = RiskAssessment.from_score(0)
        assert assessment.fraud_flags == []

    def test_copies_flags_defensively(self):
        flags = ["high_amount"]
        assessment = RiskAssessment.from_score(30, flags)
        flags.append("mutated")
        assert assessment.fraud_flags == ["high_amount"]

    def test_negative_score_raises(self):
        with pytest.raises(ValueError):
            RiskAssessment.from_score(-5)


class TestRiskAssessmentFromOutcomes:
    def test_aggregates_only_triggered_rules(self):
        outcomes = [
            RuleOutcome(name="high_amount", risk_points=30, triggered=True),
            RuleOutcome(name="high_velocity", risk_points=40, triggered=False),
            RuleOutcome(name="unusual_time", risk_points=20, triggered=True),
        ]
        assessment = RiskAssessment.from_outcomes(outcomes)
        assert assessment.risk_score == 50
        assert assessment.fraud_flags == ["high_amount", "unusual_time"]
        assert assessment.risk_level == RiskLevel.MEDIUM

    def test_preserves_evaluation_order_of_flags(self):
        outcomes = [
            RuleOutcome(name="first", risk_points=10, triggered=True),
            RuleOutcome(name="second", risk_points=10, triggered=True),
        ]
        assessment = RiskAssessment.from_outcomes(outcomes)
        assert assessment.fraud_flags == ["first", "second"]

    def test_no_triggers_yields_low(self):
        outcomes = [
            RuleOutcome(name="high_amount", risk_points=30, triggered=False),
        ]
        assessment = RiskAssessment.from_outcomes(outcomes)
        assert assessment.risk_score == 0
        assert assessment.fraud_flags == []
        assert assessment.risk_level == RiskLevel.LOW

    def test_empty_outcomes_yields_low(self):
        assessment = RiskAssessment.from_outcomes([])
        assert assessment.risk_score == 0
        assert assessment.risk_level == RiskLevel.LOW


class TestRiskAssessmentSerialization:
    def test_to_dict_round_trips_fields(self):
        assessment = RiskAssessment.from_score(80, ["high_amount"])
        assert assessment.to_dict() == {
            "risk_score": 80,
            "risk_level": RiskLevel.HIGH,
            "status": TransactionStatus.HELD,
            "fraud_flags": ["high_amount"],
        }

    def test_to_dict_returns_independent_flag_list(self):
        assessment = RiskAssessment.from_score(30, ["high_amount"])
        payload = assessment.to_dict()
        payload["fraud_flags"].append("mutated")
        assert assessment.fraud_flags == ["high_amount"]

    def test_is_immutable(self):
        assessment = RiskAssessment.from_score(10)
        with pytest.raises(dataclasses.FrozenInstanceError):
            assessment.risk_score = 99  # type: ignore[misc]


class TestRiskBreakdown:
    def test_from_counts_maps_each_level(self):
        breakdown = RiskBreakdown.from_counts(
            {RiskLevel.LOW: 5, RiskLevel.MEDIUM: 3, RiskLevel.HIGH: 2}
        )
        assert (breakdown.low, breakdown.medium, breakdown.high) == (5, 3, 2)

    def test_from_counts_defaults_missing_levels_to_zero(self):
        breakdown = RiskBreakdown.from_counts({RiskLevel.HIGH: 4})
        assert breakdown.low == 0
        assert breakdown.medium == 0
        assert breakdown.high == 4

    def test_total_sums_levels(self):
        breakdown = RiskBreakdown(low=5, medium=3, high=2)
        assert breakdown.total == 10

    def test_as_dict_uses_enum_values_as_keys(self):
        breakdown = RiskBreakdown(low=5, medium=3, high=2)
        assert breakdown.as_dict() == {"LOW": 5, "MEDIUM": 3, "HIGH": 2}

    def test_empty_breakdown_defaults_to_zero(self):
        breakdown = RiskBreakdown()
        assert breakdown.total == 0


class TestDashboardStatsAverageReview:
    def test_averages_complete_pairs(self):
        base = datetime(2026, 1, 1, 9, 0, 0)
        intervals = [
            (base, base + timedelta(minutes=10)),
            (base, base + timedelta(minutes=20)),
        ]
        assert DashboardStats.average_review_minutes(intervals) == 15.0

    def test_empty_returns_zero(self):
        assert DashboardStats.average_review_minutes([]) == 0.0

    def test_skips_pairs_with_missing_timestamp(self):
        base = datetime(2026, 1, 1, 9, 0, 0)
        intervals = [
            (base, base + timedelta(minutes=30)),
            (None, base + timedelta(minutes=30)),
            (base, None),
        ]
        assert DashboardStats.average_review_minutes(intervals) == 30.0

    def test_all_incomplete_returns_zero(self):
        base = datetime(2026, 1, 1, 9, 0, 0)
        assert DashboardStats.average_review_minutes([(None, base)]) == 0.0

    def test_consumes_a_generator(self):
        base = datetime(2026, 1, 1, 9, 0, 0)
        gen = ((base, base + timedelta(minutes=6)) for _ in range(3))
        assert DashboardStats.average_review_minutes(gen) == 6.0


class TestTransactionDraft:
    def _draft(self, **overrides) -> TransactionDraft:
        defaults = dict(
            account_number="**** 4521",
            account_holder_name="John Smith",
            amount=Decimal("1234.56"),
            merchant_name="Test Merchant",
            merchant_category="Retail",
            transaction_type="CARD",
            location_city="New York",
            location_country="US",
            latitude=40.7128,
            longitude=-74.0060,
            timestamp=datetime(2026, 1, 2, 3, 4, 5),
        )
        defaults.update(overrides)
        return TransactionDraft(**defaults)

    def test_payload_stringifies_amount(self):
        payload = self._draft().to_api_payload()
        assert payload["amount"] == "1234.56"
        assert isinstance(payload["amount"], str)

    def test_payload_iso_formats_timestamp(self):
        payload = self._draft().to_api_payload()
        assert payload["timestamp"] == "2026-01-02T03:04:05"

    def test_payload_contains_all_api_fields(self):
        payload = self._draft().to_api_payload()
        expected_keys = {
            "account_number",
            "account_holder_name",
            "amount",
            "merchant_name",
            "merchant_category",
            "transaction_type",
            "location_city",
            "location_country",
            "latitude",
            "longitude",
            "timestamp",
        }
        assert set(payload.keys()) == expected_keys

    def test_payload_preserves_optional_coordinates_as_none(self):
        payload = self._draft(latitude=None, longitude=None).to_api_payload()
        assert payload["latitude"] is None
        assert payload["longitude"] is None

    def test_is_immutable(self):
        draft = self._draft()
        with pytest.raises(dataclasses.FrozenInstanceError):
            draft.amount = Decimal("1.00")  # type: ignore[misc]
