import logging
from typing import List

from app.events.bus import EventBus, Unsubscribe
from app.events.event_types import (
    TransactionCreated,
    TransactionHeld,
    TransactionReviewed,
)

# Dedicated audit logger so transaction lifecycle events can be routed or
# filtered independently of the rest of the application's logging.
audit_logger = logging.getLogger("app.audit")


def log_transaction_created(event: TransactionCreated) -> None:
    audit_logger.info(
        "transaction_created id=%s account=%s amount=%s risk=%s score=%s status=%s",
        event.transaction_id,
        event.account_number,
        event.amount,
        event.risk_level,
        event.risk_score,
        event.status,
    )


def log_transaction_held(event: TransactionHeld) -> None:
    audit_logger.warning(
        "transaction_held id=%s account=%s score=%s flags=%s",
        event.transaction_id,
        event.account_number,
        event.risk_score,
        ",".join(event.fraud_flags) or "none",
    )


def log_transaction_reviewed(event: TransactionReviewed) -> None:
    audit_logger.info(
        "transaction_reviewed id=%s decision=%s reviewed_by=%s",
        event.transaction_id,
        event.decision,
        event.reviewed_by,
    )


def register_default_subscribers(bus: EventBus) -> List[Unsubscribe]:
    """Attach the built-in audit subscribers to ``bus``.

    Returns the unsubscribe handles so a caller (for example a test) can tear
    the subscriptions down again.
    """
    return [
        bus.subscribe(TransactionCreated, log_transaction_created),
        bus.subscribe(TransactionHeld, log_transaction_held),
        bus.subscribe(TransactionReviewed, log_transaction_reviewed),
    ]
