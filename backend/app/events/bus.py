import logging
import threading
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Type, TypeVar

from app.events.event_types import Event

logger = logging.getLogger(__name__)

E = TypeVar("E", bound=Event)

# A handler receives a single event instance and returns nothing.
Handler = Callable[[E], None]

# Returned by ``subscribe`` so callers can detach without holding onto the
# original event type / handler pair.
Unsubscribe = Callable[[], None]


def _validate_event_type(event_type: object) -> None:
    """Guard against subscribing/publishing against a non-event type.

    Registering a handler for something that is not an ``Event`` subclass can
    never receive a delivery (dispatch walks an event's MRO), so it is almost
    certainly a mistake. Rejecting it here turns a silent no-op into a loud,
    early failure at the call site.
    """
    if not isinstance(event_type, type) or not issubclass(event_type, Event):
        raise TypeError(
            f"event_type must be a subclass of Event, got {event_type!r}"
        )


def _validate_handler(handler: object) -> None:
    if not callable(handler):
        raise TypeError(f"handler must be callable, got {handler!r}")


class EventBus:
    """A lightweight, thread-safe, in-process publish/subscribe bus.

    Handlers are registered against an event *type*. When an event is
    published, every handler registered for that type -- or for any of its
    base classes -- is invoked synchronously with the event instance. Because
    dispatch walks the class hierarchy, subscribing to :class:`Event` acts as a
    catch-all for every event on the bus.

    Delivery is best-effort and isolated: if one handler raises, the exception
    is logged and the remaining handlers still run. This keeps a single buggy
    subscriber from breaking the flow that published the event.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[Type[Event], List[Handler]] = defaultdict(list)
        self._lock = threading.RLock()

    def subscribe(self, event_type: Type[E], handler: Handler) -> Unsubscribe:
        """Register ``handler`` for ``event_type``.

        Registering the same handler for the same type twice is a no-op, so
        callers do not accidentally receive duplicate deliveries. Returns a
        callable that removes this subscription when invoked.

        Raises ``TypeError`` if ``event_type`` is not an :class:`Event`
        subclass or ``handler`` is not callable.
        """
        _validate_event_type(event_type)
        _validate_handler(handler)
        with self._lock:
            handlers = self._subscribers[event_type]
            if handler not in handlers:
                handlers.append(handler)

        def _unsubscribe() -> None:
            self.unsubscribe(event_type, handler)

        return _unsubscribe

    def unsubscribe(self, event_type: Type[E], handler: Handler) -> bool:
        """Remove a previously registered handler.

        Returns ``True`` if a subscription was removed, ``False`` if the
        handler was not registered for that type. Raises ``TypeError`` if
        ``event_type`` is not an :class:`Event` subclass.
        """
        _validate_event_type(event_type)
        with self._lock:
            handlers = self._subscribers.get(event_type)
            if not handlers or handler not in handlers:
                return False
            handlers.remove(handler)
            if not handlers:
                del self._subscribers[event_type]
            return True

    def publish(self, event: Event) -> int:
        """Deliver ``event`` to all matching handlers.

        Handlers registered for the event's exact type and for any of its base
        classes are invoked in registration order. A handler that is
        registered for more than one class in the event's hierarchy is still
        invoked at most once per publish. Returns the number of handlers that
        completed without raising.

        Raises ``TypeError`` if ``event`` is not an :class:`Event` instance.
        """
        if not isinstance(event, Event):
            raise TypeError(f"event must be an Event instance, got {event!r}")
        handlers = self._handlers_for(type(event))
        delivered = 0
        for handler in handlers:
            try:
                handler(event)
            except Exception:  # noqa: BLE001 - isolate subscriber failures
                logger.exception(
                    "Event handler %r failed while handling %s",
                    handler,
                    type(event).__name__,
                )
            else:
                delivered += 1
        return delivered

    def on(self, event_type: Type[E]) -> Callable[[Handler], Handler]:
        """Decorator form of :meth:`subscribe`.

        Registers the decorated function and returns it unchanged so it can
        still be called directly (and unsubscribed later).
        """
        _validate_event_type(event_type)

        def _decorator(handler: Handler) -> Handler:
            self.subscribe(event_type, handler)
            return handler

        return _decorator

    def subscriber_count(self, event_type: Type[E]) -> int:
        """Number of handlers registered for exactly ``event_type``."""
        _validate_event_type(event_type)
        with self._lock:
            return len(self._subscribers.get(event_type, ()))

    def clear(self, event_type: Optional[Type[E]] = None) -> None:
        """Remove subscriptions, primarily useful for test isolation.

        With no argument every subscription is removed. Passing an
        ``event_type`` removes only the handlers registered for exactly that
        type, leaving handlers on its base or derived classes untouched.
        """
        if event_type is not None:
            _validate_event_type(event_type)
        with self._lock:
            if event_type is None:
                self._subscribers.clear()
            else:
                self._subscribers.pop(event_type, None)

    def _handlers_for(self, event_type: Type[Event]) -> List[Handler]:
        """Snapshot the handlers matching ``event_type`` and its bases.

        A snapshot is taken under the lock so that handlers which subscribe or
        unsubscribe during delivery cannot mutate the list mid-iteration.

        Handlers are collected in MRO order (most specific type first) and
        de-duplicated: a handler registered for both a class and one of its
        bases is only invoked once, matching the idempotency guarantee that
        ``subscribe`` already provides within a single type.
        """
        with self._lock:
            collected: List[Handler] = []
            for klass in event_type.__mro__:
                for handler in self._subscribers.get(klass, ()):
                    if handler not in collected:
                        collected.append(handler)
            return collected


# Default process-wide bus. Application code should import and use this
# instance so that publishers and subscribers share the same registry.
event_bus = EventBus()
