from app.services.transaction_id import normalize_transaction_id


def test_normalize_transaction_id_trims_and_uppercases():
    assert normalize_transaction_id("  txn-test-001  ") == "TXN-TEST-001"


def test_normalize_transaction_id_returns_none_for_blank():
    assert normalize_transaction_id("   ") is None


def test_normalize_transaction_id_returns_none_for_none():
    assert normalize_transaction_id(None) is None


def test_normalize_transaction_id_strips_prefix_when_requested():
    assert normalize_transaction_id("TXN-123", include_prefix=False) == "123"
    assert normalize_transaction_id("txn-123", include_prefix=False) == "123"
    assert normalize_transaction_id("NO-PREFIX-123", include_prefix=False) == "NO-PREFIX-123"
