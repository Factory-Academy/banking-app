from sqlalchemy.orm import Session
from sqlalchemy import func
from app.exceptions import TransactionNotFoundError
from app.models.transaction import Transaction
from app.services.transaction_id import normalize_transaction_id


def get_transaction_or_raise(db: Session, transaction_id: str) -> Transaction:
    """Fetch a transaction by id or raise a domain exception."""
    normalized_id = normalize_transaction_id(transaction_id)
    if normalized_id is None:
        raise TransactionNotFoundError(transaction_id=transaction_id or "")

    transaction = db.query(Transaction).filter(func.upper(Transaction.id) == normalized_id).first()
    if not transaction:
        raise TransactionNotFoundError(transaction_id=transaction_id)
    return transaction
