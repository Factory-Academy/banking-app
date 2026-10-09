from app.services.transaction_id import normalize_transaction_id


def test_normalize_transaction_id_trims_and_uppercases():
    assert normalize_transaction_id("  txn-test-001  ") == "TXN-TEST-001"


def test_normalize_transaction_id_returns_none_for_blank():
    assert normalize_transaction_id("   ") is None


def test_normalize_transaction_id_returns_none_for_none():
    assert normalize_transaction_id(None) is None
