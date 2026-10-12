import uuid
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import RateLimitExceededError
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate
from app.services.fraud_detection import FraudDetectionService
from app.utils.resilience import RateLimiter

# Process-wide limiter shared by all requests. Keyed by account number so a
# single noisy account cannot exhaust the submission path for everyone else.
_default_rate_limiter = RateLimiter(
    capacity=settings.rate_limit_capacity,
    refill_rate=settings.rate_limit_refill_rate,
)


def get_rate_limiter() -> RateLimiter:
    """Return the shared submission rate limiter."""
    return _default_rate_limiter


def submit_transaction(
    db: Session,
    transaction: TransactionCreate,
    *,
    rate_limiter: Optional[RateLimiter] = None,
    fraud_service: Optional[FraudDetectionService] = None,
) -> Transaction:
    """Create a transaction after enforcing the per-account rate limit.

    The ``rate_limiter`` and ``fraud_service`` arguments are injectable so the
    behaviour can be driven deterministically in tests.

    Raises:
        RateLimitExceededError: when the account has exhausted its allowance.
    """
    if settings.rate_limit_enabled:
        limiter = rate_limiter or _default_rate_limiter
        result = limiter.allow(transaction.account_number)
        if not result.allowed:
            raise RateLimitExceededError(
                key=transaction.account_number,
                retry_after=result.retry_after,
            )

    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"

    account_history = (
        db.query(Transaction)
        .filter(Transaction.account_number == transaction.account_number)
        .order_by(desc(Transaction.timestamp))
        .all()
    )

    new_txn = Transaction(id=txn_id, **transaction.model_dump())

    service = fraud_service or FraudDetectionService()
    risk_assessment = service.analyze_transaction(new_txn, account_history)

    new_txn.risk_score = risk_assessment["risk_score"]
    new_txn.risk_level = risk_assessment["risk_level"]
    new_txn.status = risk_assessment["status"]
    new_txn.fraud_flags = risk_assessment["fraud_flags"]

    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)

    return new_txn
