from sqlalchemy.orm import Session
from app.exceptions import TransactionNotFoundError
from app.models.transaction import Transaction


def get_transaction_or_raise(db: Session, transaction_id: str) -> Transaction:
    """Fetch a transaction by id or raise a domain exception."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise TransactionNotFoundError(transaction_id=transaction_id)
    return transaction
