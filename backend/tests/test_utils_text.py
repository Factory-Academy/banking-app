import pytest

from app.utils.text import slugify


@pytest.mark.parametrize(
    "value, expected",
    [
        ("Hello World", "hello-world"),
        ("  Already-Slugged  ", "already-slugged"),
        ("Banking App v2!", "banking-app-v2"),
        ("***", ""),
        (None, ""),
    ],
)
def test_slugify(value, expected):
    assert slugify(value) == expected
