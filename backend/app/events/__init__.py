"""In-process pub/sub event system.

Publish typed :class:`DomainEvent` instances on the shared :data:`event_bus`
and register handlers with :meth:`EventBus.subscribe`. See ``docs/NOTES.md`` for
a usage walkthrough.
"""
from app.events.bus import (
    EventBus,
    Handler,
    HandlerError,
    PublishResult,
    Subscription,
    event_bus,
)
from app.events.event_types import (
    DomainEvent,
    TransactionCreated,
    TransactionHeld,
    TransactionReviewed,
)
from app.events.subscribers import register_default_subscribers

__all__ = [
    "EventBus",
    "Subscription",
    "PublishResult",
    "HandlerError",
    "Handler",
    "event_bus",
    "DomainEvent",
    "TransactionCreated",
    "TransactionHeld",
    "TransactionReviewed",
    "register_default_subscribers",
]
