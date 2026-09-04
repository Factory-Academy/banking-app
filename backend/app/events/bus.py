"""A lightweight, thread-safe, in-process publish/subscribe event bus.

The bus dispatches :class:`~app.events.event_types.DomainEvent` instances to
handlers that subscribed for that event's type. Dispatch walks the event's MRO,
so a subscriber registered for a base class (e.g. ``DomainEvent`` itself) also
receives every subclass event, and exact-type subscribers are notified before
base-type subscribers.

Design goals:

* **Typed** - subscriptions are keyed on the event class, not a magic string.
* **Isolated** - one failing handler never prevents the others from running;
  errors are collected and reported on the returned :class:`PublishResult`.
* **Deterministic** - handlers fire in subscription order.
* **Thread-safe** - subscribe/unsubscribe/publish may be called concurrently.
"""
from __future__ import annotations

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Type, TypeVar

from app.events.event_types import DomainEvent

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=DomainEvent)
Handler = Callable[[E], None]


class Subscription:
    """A handle to a registered handler.

    Callers keep the returned instance to cancel the subscription later via
    :meth:`unsubscribe`. Cancellation is idempotent and thread-safe.
    """

    __slots__ = ("event_type", "handler", "once", "_bus", "_active")

    def __init__(
        self,
        event_type: Type[DomainEvent],
        handler: Handler,
        once: bool,
        bus: "EventBus",
    ) -> None:
        self.event_type = event_type
        self.handler = handler
        self.once = once
        self._bus = bus
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def unsubscribe(self) -> None:
        """Detach this handler from the bus. Safe to call more than once."""
        if self._active:
            self._active = False
            self._bus._remove(self)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        state = "active" if self._active else "cancelled"
        return (
            f"<Subscription {self.event_type.__name__} "
            f"once={self.once} {state}>"
        )


@dataclass
class HandlerError:
    """Captures a single handler failure during a publish."""

    subscription: Subscription
    exception: Exception


@dataclass
class PublishResult:
    """Outcome of a single :meth:`EventBus.publish` call."""

    event: DomainEvent
    handled: int = 0
    errors: List[HandlerError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when every notified handler completed without raising."""
        return not self.errors


class EventBus:
    """An in-process pub/sub broker for :class:`DomainEvent` instances."""

    def __init__(self, *, raise_on_error: bool = False) -> None:
        self._subscribers: Dict[Type[DomainEvent], List[Subscription]] = defaultdict(list)
        self._lock = threading.RLock()
        self._raise_on_error = raise_on_error

    def subscribe(
        self,
        event_type: Type[E],
        handler: Handler[E],
        *,
        once: bool = False,
    ) -> Subscription:
        """Register ``handler`` for ``event_type`` (and its subclasses).

        Args:
            event_type: A :class:`DomainEvent` subclass. Use ``DomainEvent`` to
                receive every event.
            handler: A callable accepting the event instance.
            once: When True, the handler is automatically unsubscribed after it
                is first invoked.

        Returns:
            A :class:`Subscription` that can be used to cancel the handler.
        """
        if not (isinstance(event_type, type) and issubclass(event_type, DomainEvent)):
            raise TypeError(
                f"event_type must be a DomainEvent subclass, got {event_type!r}"
            )
        if not callable(handler):
            raise TypeError(f"handler must be callable, got {handler!r}")

        sub = Subscription(event_type, handler, once, self)
        with self._lock:
            self._subscribers[event_type].append(sub)
        return sub

    def subscribe_all(self, handler: Handler[DomainEvent], *, once: bool = False) -> Subscription:
        """Subscribe ``handler`` to every event regardless of type."""
        return self.subscribe(DomainEvent, handler, once=once)

    def _remove(self, sub: Subscription) -> None:
        with self._lock:
            handlers = self._subscribers.get(sub.event_type)
            if not handlers:
                return
            try:
                handlers.remove(sub)
            except ValueError:
                return
            if not handlers:
                del self._subscribers[sub.event_type]

    def publish(self, event: DomainEvent) -> PublishResult:
        """Dispatch ``event`` to all matching handlers in subscription order.

        Handlers subscribed to the event's exact type run first, followed by
        handlers subscribed to progressively more general base classes. A
        handler that raises is logged and recorded on the result; remaining
        handlers still run unless the bus was created with
        ``raise_on_error=True``.
        """
        if not isinstance(event, DomainEvent):
            raise TypeError(f"event must be a DomainEvent, got {event!r}")

        # Snapshot the matching handlers under the lock so that a handler which
        # subscribes or unsubscribes during dispatch cannot mutate the list we
        # are iterating over.
        with self._lock:
            matched: List[Subscription] = []
            for klass in type(event).__mro__:
                if not (isinstance(klass, type) and issubclass(klass, DomainEvent)):
                    continue
                matched.extend(self._subscribers.get(klass, ()))

        result = PublishResult(event=event)
        for sub in matched:
            if not sub.active:
                continue
            try:
                sub.handler(event)
                result.handled += 1
            except Exception as exc:  # noqa: BLE001 - deliberate isolation
                logger.exception(
                    "Handler %r failed while processing %s",
                    sub.handler,
                    event.name,
                )
                result.errors.append(HandlerError(subscription=sub, exception=exc))
                if self._raise_on_error:
                    if sub.once:
                        sub.unsubscribe()
                    raise
            finally:
                if sub.once and sub.active:
                    sub.unsubscribe()

        return result

    def subscriber_count(self, event_type: Optional[Type[DomainEvent]] = None) -> int:
        """Number of active subscriptions, optionally for a single event type."""
        with self._lock:
            if event_type is not None:
                return len(self._subscribers.get(event_type, ()))
            return sum(len(subs) for subs in self._subscribers.values())

    def clear(self, event_type: Optional[Type[DomainEvent]] = None) -> None:
        """Remove all subscriptions, or only those for ``event_type``."""
        with self._lock:
            if event_type is not None:
                subs = self._subscribers.pop(event_type, [])
            else:
                subs = [s for group in self._subscribers.values() for s in group]
                self._subscribers.clear()
        for sub in subs:
            sub._active = False


# Application-wide default bus. Import this instance to publish or subscribe
# from anywhere in the app; tests may create their own EventBus in isolation.
event_bus = EventBus()


__all__ = [
    "EventBus",
    "Subscription",
    "PublishResult",
    "HandlerError",
    "Handler",
    "event_bus",
]
