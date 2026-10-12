import pytest

from app.utils.resilience._validation import require_non_negative, require_positive


@pytest.mark.parametrize("value,expected", [(1, 1.0), (2.5, 2.5), (0.1, 0.1)])
def test_require_positive_accepts_and_coerces_to_float(value, expected):
    result = require_positive(value, "value")
    assert result == pytest.approx(expected)
    assert isinstance(result, float)


@pytest.mark.parametrize("value", [0, -1, -0.5])
def test_require_positive_rejects_non_positive(value):
    with pytest.raises(ValueError):
        require_positive(value, "value")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_require_positive_rejects_non_finite(value):
    with pytest.raises(ValueError):
        require_positive(value, "value")


def test_require_non_negative_accepts_zero():
    assert require_non_negative(0, "value") == 0.0


@pytest.mark.parametrize("value", [-1, -0.0001])
def test_require_non_negative_rejects_negative(value):
    with pytest.raises(ValueError):
        require_non_negative(value, "value")


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_require_non_negative_rejects_non_finite(value):
    with pytest.raises(ValueError):
        require_non_negative(value, "value")


@pytest.mark.parametrize("value", [None, "abc", object()])
def test_rejects_values_that_are_not_numbers(value):
    with pytest.raises(ValueError):
        require_positive(value, "value")


def test_error_message_includes_the_field_name():
    with pytest.raises(ValueError, match="widgets"):
        require_positive(-1, "widgets")
