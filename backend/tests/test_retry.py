import pytest

from app.utils.retry import retry


def test_retry_returns_value_on_first_attempt():
    assert retry(lambda: "ok") == "ok"


def test_retry_retries_then_succeeds():
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise ValueError("temporary")
        return "ok"

    assert retry(flaky, attempts=3, retry_on=ValueError) == "ok"
    assert calls["count"] == 3


def test_retry_raises_after_exhausting_attempts():
    def always_fails():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        retry(always_fails, attempts=2, retry_on=ValueError)
