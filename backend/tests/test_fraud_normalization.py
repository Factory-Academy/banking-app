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
    def test_passes_through_decimal(self):
        assert safe_decimal(Decimal("1500.50")) == Decimal("1500.50")

    def test_coerces_int_and_float_and_str(self):
        assert safe_decimal(10) == Decimal("10")
        assert safe_decimal("250.75") == Decimal("250.75")
        assert safe_decimal(99.5) == Decimal(str(99.5))

    def test_none_returns_none(self):
        assert safe_decimal(None) is None

    def test_non_numeric_string_returns_none(self):
        assert safe_decimal("not-a-number") is None
        assert safe_decimal("") is None

    def test_bool_rejected(self):
        # bool is an int subclass; treating True as 1 would corrupt amounts.
        assert safe_decimal(True) is None
        assert safe_decimal(False) is None

    def test_nan_and_infinity_rejected(self):
        assert safe_decimal(Decimal("NaN")) is None
        assert safe_decimal(Decimal("Infinity")) is None
        assert safe_decimal(float("inf")) is None
        assert safe_decimal(float("nan")) is None


class TestSafeTimestamp:
    def test_passes_through_datetime(self):
        ts = datetime(2024, 1, 1, 3, 30)
        assert safe_timestamp(ts) is ts

    @pytest.mark.parametrize("value", [None, "2024-01-01", 1700000000, 3.14])
    def test_non_datetime_returns_none(self, value):
        assert safe_timestamp(value) is None


class TestNormalizeCountry:
    def test_uppercases_and_strips(self):
        assert normalize_country(" us ") == "US"
        assert normalize_country("gb") == "GB"

    def test_empty_or_whitespace_returns_none(self):
        assert normalize_country("") is None
        assert normalize_country("   ") is None

    @pytest.mark.parametrize("value", [None, 123, ["US"]])
    def test_non_string_returns_none(self, value):
        assert normalize_country(value) is None

    def test_is_home_country(self):
        assert is_home_country("us") is True
        assert is_home_country(HOME_COUNTRY) is True
        assert is_home_country("CN") is False
        assert is_home_country(None) is False
