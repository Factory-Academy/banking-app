from datetime import datetime
from decimal import Decimal

import pytest

from app.services.fraud.normalization import (
    HOME_COUNTRY,
    is_home_country,
    normalize_country,
    safe_decimal,
    safe_timestamp,
)


class TestSafeDecimal:
    def test_none_returns_none(self):
        assert safe_decimal(None) is None

    def test_bool_returns_none(self):
        # bool is a subclass of int; it is never a valid amount.
        assert safe_decimal(True) is None
        assert safe_decimal(False) is None

    def test_passes_through_finite_decimal(self):
        assert safe_decimal(Decimal("12.50")) == Decimal("12.50")

    def test_nan_returns_none(self):
        assert safe_decimal(Decimal("NaN")) is None
        assert safe_decimal(float("nan")) is None

    def test_infinity_returns_none(self):
        assert safe_decimal(float("inf")) is None
        assert safe_decimal(Decimal("Infinity")) is None

    def test_numeric_string(self):
        assert safe_decimal("1000.00") == Decimal("1000.00")

    def test_garbage_string_returns_none(self):
        assert safe_decimal("not-a-number") is None

    def test_int_and_float(self):
        assert safe_decimal(5) == Decimal("5")
        assert safe_decimal(2.5) == Decimal("2.5")

    @pytest.mark.parametrize("value", [object(), [1, 2], {"a": 1}])
    def test_unsupported_types_return_none(self, value):
        assert safe_decimal(value) is None


class TestSafeTimestamp:
    def test_datetime_passes_through(self):
        now = datetime(2025, 1, 1, 12, 0)
        assert safe_timestamp(now) is now

    @pytest.mark.parametrize("value", [None, "2025-01-01", 1735732800, object()])
    def test_non_datetime_returns_none(self, value):
        assert safe_timestamp(value) is None


class TestNormalizeCountry:
    def test_strips_and_uppercases(self):
        assert normalize_country("  us ") == "US"

    def test_empty_or_whitespace_returns_none(self):
        assert normalize_country("") is None
        assert normalize_country("   ") is None

    @pytest.mark.parametrize("value", [None, 5, object(), ["US"]])
    def test_non_string_returns_none(self, value):
        assert normalize_country(value) is None


class TestIsHomeCountry:
    def test_home_country_constant(self):
        assert HOME_COUNTRY == "US"

    def test_case_insensitive_match(self):
        assert is_home_country("us") is True
        assert is_home_country("  US ") is True

    def test_non_home(self):
        assert is_home_country("GB") is False

    def test_none_is_not_home(self):
        assert is_home_country(None) is False
