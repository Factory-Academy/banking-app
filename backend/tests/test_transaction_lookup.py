import pytest

from app.exceptions import TransactionNotFoundError
from app.services.transaction_lookup import get_transaction_or_raise


def test_get_transaction_or_raise_returns_transaction(db_session, sample_transaction):
    transaction = get_transaction_or_raise(db=db_session, transaction_id=sample_transaction.id)
    assert transaction.id == sample_transaction.id


def test_get_transaction_or_raise_normalizes_transaction_id(db_session, sample_transaction):
    transaction = get_transaction_or_raise(
        db=db_session,
        transaction_id=f"  {sample_transaction.id.lower()}  ",
    )
    assert transaction.id == sample_transaction.id


def test_get_transaction_or_raise_raises_not_found(db_session):
    with pytest.raises(TransactionNotFoundError) as exc:
        get_transaction_or_raise(db=db_session, transaction_id="TXN-DOES-NOT-EXIST")
    assert str(exc.value) == "Transaction not found"


def test_get_transaction_or_raise_raises_not_found_for_blank_id(db_session):
    with pytest.raises(TransactionNotFoundError) as exc:
        get_transaction_or_raise(db=db_session, transaction_id="   ")
    assert str(exc.value) == "Transaction not found"


def test_get_account_history_returns_404_for_missing_transaction(client):
    response = client.get("/api/v1/transactions/TXN-DOES-NOT-EXIST/history")
    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found"}
