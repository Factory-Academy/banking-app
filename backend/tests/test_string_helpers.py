from app.utils.string_helpers import slugify


def test_slugify_basic_phrase():
    assert slugify("Hello World") == "hello-world"


def test_slugify_trims_and_collapses_separators():
    assert slugify("  hello___world   test  ") == "hello-world-test"


def test_slugify_removes_special_characters():
    assert slugify("Payment #42: Approved!") == "payment-42-approved"


def test_slugify_none_returns_empty_string():
    assert slugify(None) == ""
