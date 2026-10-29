import pytest
from app.utils.helpers import slugify


def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_multiple_spaces():
    assert slugify("Multiple   Spaces   Here") == "multiple-spaces-here"


def test_slugify_special_characters():
    assert slugify("Special@#Characters!") == "special-characters"


def test_slugify_mixed_case():
    assert slugify("MixedCaseString") == "mixedcasestring"


def test_slugify_numbers():
    assert slugify("Product 123") == "product-123"


def test_slugify_leading_trailing_spaces():
    assert slugify("  Leading and Trailing  ") == "leading-and-trailing"


def test_slugify_empty_string():
    assert slugify("") == ""


def test_slugify_only_special_characters():
    assert slugify("@#$%^&*()") == ""


def test_slugify_hyphens_already_present():
    assert slugify("already-has-hyphens") == "already-has-hyphens"


def test_slugify_underscores():
    assert slugify("under_score_text") == "under-score-text"
