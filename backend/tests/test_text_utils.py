from app.utils.text import slugify


def test_slugify_converts_to_lowercase_hyphenated_ascii():
    assert slugify("  Café Payment Review 2026!  ") == "cafe-payment-review-2026"


def test_slugify_collapses_repeated_separators():
    assert slugify("fraud---alerts___high risk") == "fraud-alerts-high-risk"


def test_slugify_returns_empty_string_when_no_alphanumeric_characters():
    assert slugify("!!!___---") == ""
