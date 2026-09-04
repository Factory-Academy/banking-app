"""Default subscribers wired onto the application event bus.

These handlers are deliberately side-effect-light (they log) so that the demo
app stays self-contained. They double as a reference for how real subscribers -
notifications, audit trails, metrics - would attach to the bus.
"""
from __future__ import annotations

import logging
from typing import List

from app.events.bus import EventBus, Subscription
from app.events.event_types import (
    TransactionCreated,
    TransactionHeld,
    TransactionReviewed,
)

logger = logging.getLogger("app.events.audit")


def log_transaction_created(event: TransactionCreated) -> None:
    logger.info(
        "transaction.created id=%s account=%s amount=%s risk=%s(%d) status=%s flags=%s",
        event.transaction_id,
        event.account_number,
        event.amount,
        event.risk_level,
        event.risk_score,
        event.status,
        ",".join(event.fraud_flags) or "-",
    )


def log_transaction_held(event: TransactionHeld) -> None:
    logger.warning(
        "transaction.held id=%s account=%s amount=%s risk_score=%d flags=%s",
        event.transaction_id,
        event.account_number,
        event.amount,
        event.risk_score,
        ",".join(event.fraud_flags) or "-",
    )


def log_transaction_reviewed(event: TransactionReviewed) -> None:
    logger.info(
        "transaction.reviewed id=%s account=%s %s->%s by=%s",
        event.transaction_id,
        event.account_number,
        event.previous_status,
        event.decision,
        event.reviewed_by,
    )


def register_default_subscribers(bus: EventBus) -> List[Subscription]:
    """Attach the built-in audit-logging handlers to ``bus``.

    Returns the created subscriptions so a caller (or a test) can detach them.
    Idempotent enough for app startup because subscriptions are cheap; callers
    that re-register should first :meth:`~app.events.bus.EventBus.clear` the bus.
    """
    return [
        bus.subscribe(TransactionCreated, log_transaction_created),
        bus.subscribe(TransactionHeld, log_transaction_held),
        bus.subscribe(TransactionReviewed, log_transaction_reviewed),
    ]


__all__ = [
    "register_default_subscribers",
    "log_transaction_created",
    "log_transaction_held",
    "log_transaction_reviewed",
]
