"""Tests for the pluggable fraud-scoring strategies and their factory."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.fraud import (
    HIGH_RISK_THRESHOLD,
    MEDIUM_RISK_THRESHOLD,
    RuleOutcome,
)
from app.models.transaction import RiskLevel, Transaction, TransactionStatus
from app.services.fraud import (
    SCORE_FLOOR,
    AdditiveScoringStrategy,
    DampenedScoringStrategy,
    ScoringStrategy,
    available_strategies,
    clamp_score,
    create_scoring_strategy,
    register_scoring_strategy,
    round_half_up,
    temporary_strategy,
    unregister_scoring_strategy,
)
from app.services.fraud_detection import FraudDetectionService


def outcome(name: str, points: int, triggered: bool) -> RuleOutcome:
    return RuleOutcome(name=name, risk_points=points, triggered=triggered)


@pytest.fixture
def base_transaction() -> Transaction:
    return Transaction(
        id="TXN-TEST-001",
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
        timestamp=datetime.utcnow(),
        status=TransactionStatus.CLEARED,
        risk_level=RiskLevel.LOW,
        risk_score=0,
        fraud_flags=[],
    )


class TestAdditiveScoringStrategy:
    def test_empty_outcomes_score_zero(self):
        assert AdditiveScoringStrategy().score([]) == 0

    def test_all_untriggered_score_zero(self):
        outcomes = [outcome("a", 30, False), outcome("b", 40, False)]
        assert AdditiveScoringStrategy().score(outcomes) == 0

    def test_single_triggered_returns_its_points(self):
        assert AdditiveScoringStrategy().score([outcome("a", 30, True)]) == 30

    def test_sums_only_triggered_rules(self):
        outcomes = [
            outcome("a", 30, True),
            outcome("b", 40, False),
            outcome("c", 20, True),
        ]
        assert AdditiveScoringStrategy().score(outcomes) == 50

    def test_order_independent(self):
        forward = [outcome("a", 30, True), outcome("b", 20, True)]
        reverse = list(reversed(forward))
        strategy = AdditiveScoringStrategy()
        assert strategy.score(forward) == strategy.score(reverse) == 50

    def test_negative_points_clamp_to_floor(self):
        # A malformed rule carrying negative points must not drive the score
        # below zero, where classify() would reject it.
        outcomes = [outcome("a", 30, True), outcome("b", -100, True)]
        assert AdditiveScoringStrategy().score(outcomes) == SCORE_FLOOR

    def test_score_is_never_negative(self):
        outcomes = [outcome("a", -50, True)]
        assert AdditiveScoringStrategy().score(outcomes) >= SCORE_FLOOR

    def test_large_sum_is_not_capped(self):
        # No upper bound: additive stays explainable even past 100.
        outcomes = [outcome("a", 80, True), outcome("b", 70, True)]
        assert AdditiveScoringStrategy().score(outcomes) == 150

    def test_name(self):
        assert AdditiveScoringStrategy.name == "additive"
        assert AdditiveScoringStrategy().name == "additive"


class TestDampenedScoringStrategy:
    def test_empty_outcomes_score_zero(self):
        assert DampenedScoringStrategy().score([]) == 0

    def test_single_triggered_matches_additive(self):
        outcomes = [outcome("a", 30, True)]
        assert DampenedScoringStrategy().score(outcomes) == 30

    def test_diminishing_returns_below_additive(self):
        outcomes = [
            outcome("a", 30, True),
            outcome("b", 25, True),
            outcome("c", 20, True),
        ]
        additive = AdditiveScoringStrategy().score(outcomes)  # 75
        dampened = DampenedScoringStrategy(decay=0.5).score(outcomes)
        # 30 + 25*0.5 + 20*0.25 = 30 + 12.5 + 5 = 47.5 -> 48 (half-up)
        assert dampened == 48
        assert dampened < additive

    def test_ranks_highest_signal_first(self):
        # Decay is applied by rank, so input order must not matter.
        ascending = [outcome("a", 20, True), outcome("b", 30, True)]
        descending = list(reversed(ascending))
        strategy = DampenedScoringStrategy(decay=0.5)
        # 30 + 20*0.5 = 40 regardless of input order.
        assert strategy.score(ascending) == strategy.score(descending) == 40

    def test_decay_of_one_equals_additive(self):
        outcomes = [
            outcome("a", 30, True),
            outcome("b", 25, True),
            outcome("c", 20, True),
        ]
        assert DampenedScoringStrategy(decay=1.0).score(outcomes) == (
            AdditiveScoringStrategy().score(outcomes)
        )

    def test_half_up_rounding(self):
        # 10 + 10*0.25 = 12.5 -> rounds up to 13, not down to 12.
        outcomes = [outcome("a", 10, True), outcome("b", 10, True)]
        assert DampenedScoringStrategy(decay=0.25).score(outcomes) == 13

    def test_ignores_untriggered(self):
        outcomes = [outcome("a", 30, True), outcome("b", 100, False)]
        assert DampenedScoringStrategy(decay=0.5).score(outcomes) == 30

    def test_negative_points_clamp_to_floor(self):
        # Negatives sort last (ranked highest-first) and still cannot push the
        # dampened aggregate below the floor.
        outcomes = [outcome("a", 10, True), outcome("b", -100, True)]
        assert DampenedScoringStrategy(decay=0.5).score(outcomes) == SCORE_FLOOR

    @pytest.mark.parametrize("bad_decay", [0.0, -0.1, 1.1, 2.0])
    def test_rejects_out_of_range_decay(self, bad_decay):
        with pytest.raises(ValueError, match="decay must be in"):
            DampenedScoringStrategy(decay=bad_decay)

    def test_name(self):
        assert DampenedScoringStrategy.name == "dampened"


class TestFactory:
    def test_default_is_additive(self):
        strategy = create_scoring_strategy()
        assert isinstance(strategy, AdditiveScoringStrategy)

    def test_create_by_name(self):
        assert isinstance(create_scoring_strategy("additive"), AdditiveScoringStrategy)
        assert isinstance(create_scoring_strategy("dampened"), DampenedScoringStrategy)

    def test_forwards_kwargs(self):
        strategy = create_scoring_strategy("dampened", decay=0.3)
        assert isinstance(strategy, DampenedScoringStrategy)
        assert strategy.decay == 0.3

    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown scoring strategy"):
            create_scoring_strategy("does-not-exist")

    def test_available_strategies_sorted(self):
        names = available_strategies()
        assert "additive" in names
        assert "dampened" in names
        assert names == sorted(names)

    def test_register_and_use_custom_strategy(self):
        name = "test-constant"
        with temporary_strategy(name, lambda: AdditiveScoringStrategy()):
            assert name in available_strategies()
            assert isinstance(
                create_scoring_strategy(name), AdditiveScoringStrategy
            )

    def test_register_duplicate_rejected(self):
        with pytest.raises(ValueError, match="already registered"):
            register_scoring_strategy("additive", lambda: AdditiveScoringStrategy())


class TestRegistryLifecycle:
    def test_unregister_removes_custom_strategy(self):
        register_scoring_strategy("test-ephemeral", lambda: AdditiveScoringStrategy())
        assert "test-ephemeral" in available_strategies()
        unregister_scoring_strategy("test-ephemeral")
        assert "test-ephemeral" not in available_strategies()

    def test_unregister_unknown_raises(self):
        with pytest.raises(KeyError):
            unregister_scoring_strategy("never-registered")

    @pytest.mark.parametrize("builtin", ["additive", "dampened"])
    def test_cannot_unregister_builtin(self, builtin):
        with pytest.raises(ValueError, match="built-in"):
            unregister_scoring_strategy(builtin)
        # The built-in survives the failed attempt.
        assert builtin in available_strategies()

    def test_temporary_strategy_cleans_up_on_error(self):
        name = "test-raises"
        with pytest.raises(RuntimeError):
            with temporary_strategy(name, lambda: AdditiveScoringStrategy()):
                assert name in available_strategies()
                raise RuntimeError("boom")
        # Registry is restored even though the body raised.
        assert name not in available_strategies()

    def test_temporary_strategy_yields_normalized_name(self):
        with temporary_strategy("  spaced-name  ", lambda: AdditiveScoringStrategy()) as key:
            assert key == "spaced-name"
            assert key in available_strategies()

    @pytest.mark.parametrize("bad_name", ["", "   ", "\t"])
    def test_register_rejects_blank_name(self, bad_name):
        with pytest.raises(ValueError, match="non-empty"):
            register_scoring_strategy(bad_name, lambda: AdditiveScoringStrategy())

    def test_register_strips_surrounding_whitespace(self):
        with temporary_strategy("  padded  ", lambda: AdditiveScoringStrategy()):
            # Looked up under the stripped key, and the padded form resolves too.
            assert "padded" in available_strategies()
            assert isinstance(create_scoring_strategy(" padded "), AdditiveScoringStrategy)

    def test_register_rejects_non_callable_builder(self):
        with pytest.raises(TypeError):
            register_scoring_strategy("test-not-callable", "not a builder")  # type: ignore[arg-type]
        assert "test-not-callable" not in available_strategies()

    def test_create_with_blank_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            create_scoring_strategy("   ")


class TestBounds:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (0.0, 0),
            (12.5, 13),
            (12.4, 12),
            (2.5, 3),  # half away from zero, not banker's rounding where
            (0.5, 1),  # round(2.5) == 2 and round(0.5) == 0
            (-0.5, -1),  # symmetric: a half below zero rounds away to -1
            (-1.5, -2),
        ],
    )
    def test_round_half_up(self, value, expected):
        assert round_half_up(value) == expected

    @pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
    def test_round_half_up_rejects_non_finite(self, bad_value):
        with pytest.raises(ValueError, match="non-finite"):
            round_half_up(bad_value)

    def test_clamp_floors_negative(self):
        assert clamp_score(-10.0) == SCORE_FLOOR
        assert clamp_score(-0.4) == SCORE_FLOOR

    def test_clamp_rounds_and_passes_through_positive(self):
        assert clamp_score(47.5) == 48
        assert clamp_score(150.0) == 150

    def test_score_floor_is_zero(self):
        assert SCORE_FLOOR == 0


class TestProtocolConformance:
    def test_strategies_satisfy_protocol(self):
        assert isinstance(AdditiveScoringStrategy(), ScoringStrategy)
        assert isinstance(DampenedScoringStrategy(), ScoringStrategy)

    def test_arbitrary_object_is_not_a_strategy(self):
        assert not isinstance(object(), ScoringStrategy)


class TestServiceIntegration:
    def _high_risk_transaction(self, base_transaction: Transaction) -> Transaction:
        # high_amount (30) + first_international (25) + unusual_time (20) = 75.
        base_transaction.amount = Decimal("15000.00")
        base_transaction.location_country = "CN"
        base_transaction.timestamp = datetime.utcnow().replace(hour=3)
        return base_transaction

    def test_default_service_uses_additive(self):
        service = FraudDetectionService()
        assert isinstance(service.scoring_strategy, AdditiveScoringStrategy)

    def test_additive_holds_stacked_signals(self, base_transaction):
        txn = self._high_risk_transaction(base_transaction)
        result = FraudDetectionService().analyze_transaction(txn, [])
        assert result.risk_score >= HIGH_RISK_THRESHOLD
        assert result.status == TransactionStatus.HELD
        assert result.risk_level == RiskLevel.HIGH

    def test_dampened_downgrades_stacked_signals(self, base_transaction):
        txn = self._high_risk_transaction(base_transaction)
        service = FraudDetectionService(DampenedScoringStrategy(decay=0.5))
        result = service.analyze_transaction(txn, [])
        # 30 + 25*0.5 + 20*0.25 = 47.5 -> 48: medium, no longer auto-held.
        assert MEDIUM_RISK_THRESHOLD <= result.risk_score < HIGH_RISK_THRESHOLD
        assert result.status == TransactionStatus.CLEARED
        assert result.risk_level == RiskLevel.MEDIUM

    def test_strategy_choice_preserves_flags(self, base_transaction):
        txn = self._high_risk_transaction(base_transaction)
        additive = FraudDetectionService().analyze_transaction(txn, [])
        dampened = FraudDetectionService(
            DampenedScoringStrategy()
        ).analyze_transaction(txn, [])
        # The rules that fired are independent of how their points are combined.
        assert set(additive.fraud_flags) == set(dampened.fraud_flags)
        assert "high_amount" in dampened.fraud_flags

    def test_with_strategy_classmethod_uses_factory(self, base_transaction):
        service = FraudDetectionService.with_strategy("dampened", decay=0.5)
        assert isinstance(service.scoring_strategy, DampenedScoringStrategy)
        assert service.scoring_strategy.decay == 0.5

    def test_single_rule_scores_identically_across_strategies(self, base_transaction):
        # Only high_amount fires: both policies must agree.
        base_transaction.amount = Decimal("15000.00")
        additive = FraudDetectionService().analyze_transaction(base_transaction, [])
        dampened = FraudDetectionService(
            DampenedScoringStrategy()
        ).analyze_transaction(base_transaction, [])
        assert additive.risk_score == dampened.risk_score == 30
