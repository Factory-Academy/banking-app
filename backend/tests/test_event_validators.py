from decimal import Decimal

import pytest

from app.events.validators import (
    freeze_flags,
    require_positive_amount,
    require_risk_score,
    require_text,
)


# ---------------------------------------------------------------------------
# require_text
# ---------------------------------------------------------------------------

class TestRequireText:
    def test_returns_value_unchanged_when_valid(self):
        assert require_text("transaction_id", "TXN-1") == "TXN-1"

    @pytest.mark.parametrize("bad", ["", "   ", "\t\n", None, 123, b"TXN-1"])
    def test_rejects_blank_or_non_string(self, bad):
        with pytest.raises(ValueError):
            require_text("transaction_id", bad)

    def test_error_names_the_field(self):
        with pytest.raises(ValueError, match="account_number"):
            require_text("account_number", "")


# ---------------------------------------------------------------------------
# require_risk_score
# ---------------------------------------------------------------------------

class TestRequireRiskScore:
    def test_returns_value_when_valid(self):
        assert require_risk_score("risk_score", 42) == 42

    def test_zero_is_allowed(self):
        assert require_risk_score("risk_score", 0) == 0

    def test_no_upper_bound_additive_rules_can_exceed_one_rule(self):
        # The fraud rules are additive, so a combined score above any single
        # rule's weight is valid rather than an error.
        assert require_risk_score("risk_score", 200) == 200

    @pytest.mark.parametrize("bad", [-1, "10", 3.5, None])
    def test_rejects_negative_or_non_int(self, bad):
        with pytest.raises(ValueError):
            require_risk_score("risk_score", bad)

    @pytest.mark.parametrize("bad", [True, False])
    def test_rejects_bool_even_though_it_is_an_int(self, bad):
        with pytest.raises(ValueError):
            require_risk_score("risk_score", bad)


# ---------------------------------------------------------------------------
# require_positive_amount
# ---------------------------------------------------------------------------

class TestRequirePositiveAmount:
    def test_returns_value_when_valid(self):
        assert require_positive_amount("amount", Decimal("100.00")) == Decimal("100.00")

    @pytest.mark.parametrize("bad", [Decimal("0"), Decimal("-0.01"), Decimal("-100")])
    def test_rejects_zero_or_negative(self, bad):
        with pytest.raises(ValueError):
            require_positive_amount("amount", bad)

    @pytest.mark.parametrize("bad", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
    def test_rejects_non_finite(self, bad):
        with pytest.raises(ValueError):
            require_positive_amount("amount", bad)

    @pytest.mark.parametrize("bad", [100, 100.0, "100.00", True, None])
    def test_rejects_non_decimal(self, bad):
        with pytest.raises(ValueError):
            require_positive_amount("amount", bad)


# ---------------------------------------------------------------------------
# freeze_flags
# ---------------------------------------------------------------------------

class TestFreezeFlags:
    def test_converts_list_to_tuple(self):
        assert freeze_flags(["a", "b"]) == ("a", "b")

    def test_result_is_a_tuple(self):
        assert isinstance(freeze_flags(["a"]), tuple)

    def test_empty_collection_is_allowed(self):
        assert freeze_flags([]) == ()
        assert freeze_flags(()) == ()

    def test_copies_from_the_source_so_later_mutation_is_ignored(self):
        source = ["high_amount"]
        frozen = freeze_flags(source)
        source.append("mutated")
        assert frozen == ("high_amount",)

    def test_accepts_a_generator(self):
        assert freeze_flags(flag for flag in ["x", "y"]) == ("x", "y")

    @pytest.mark.parametrize("bad", ["high_amount", b"high_amount"])
    def test_rejects_a_bare_string(self, bad):
        # A bare string would otherwise explode into one flag per character.
        with pytest.raises(TypeError):
            freeze_flags(bad)

    @pytest.mark.parametrize("bad", [["ok", ""], ["ok", "   "], ["ok", 5], ["ok", None]])
    def test_rejects_empty_or_non_string_elements(self, bad):
        with pytest.raises(ValueError):
            freeze_flags(bad)
