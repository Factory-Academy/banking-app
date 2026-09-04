from app.utils import slugify


def test_slugify_normalizes_whitespace_and_case():
    assert slugify("  Hello Banking App  ") == "hello-banking-app"


def test_slugify_removes_special_characters():
    assert slugify("Risk & Fraud: Score!") == "risk-fraud-score"
