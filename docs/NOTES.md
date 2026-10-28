# In-Process Event Bus

A lightweight, thread-safe publish/subscribe module for decoupling side effects
(auditing, notifications, metrics) from the request path. It lives in
`backend/app/events/` and runs entirely in-process, with synchronous delivery
and no external broker.

## Why

The transaction routes already do one job well: validate input, score fraud,
and persist. Bolting audit logging, notifications, and future side effects
directly onto those handlers would tangle unrelated concerns together. The
event bus lets a flow announce *what happened* and lets independent subscribers
decide *what to do about it*.

## Modules

| File | Responsibility |
| --- | --- |
| `event_types.py` | Immutable, validated event value objects. |
| `bus.py` | `EventBus` dispatch plus the shared `event_bus` singleton. |
| `subscribers.py` | Built-in audit subscribers and `register_default_subscribers`. |
| `__init__.py` | Public surface (`event_bus`, event classes, helpers). |

## Events

All events subclass `Event`, a frozen dataclass that stamps `occurred_at`
(keyword-only) at construction. Events are immutable value objects describing
something that already happened:

- `TransactionCreated` - a transaction was created and scored.
- `TransactionHeld` - a transaction was auto-held as HIGH risk.
- `TransactionReviewed` - an analyst reached a decision.

Each event validates itself in `__post_init__`: identifier fields must be
non-empty strings, `risk_score` must be a non-negative integer, and
`fraud_flags` is copied into an immutable tuple so a subscriber cannot mutate a
list shared with other subscribers.

## Dispatch semantics

- **Type-based.** Handlers subscribe to an event *type*. Publishing walks the
  event's MRO, so subscribing to `Event` is a catch-all for every event.
- **De-duplicated.** A handler registered for both a class and one of its bases
  is invoked at most once per publish. Subscribing the same handler to the same
  type twice is a no-op.
- **Isolated.** If a handler raises, the exception is logged and the remaining
  handlers still run. `publish` returns the number of handlers that completed
  without raising, so a buggy subscriber never breaks the publishing flow.
- **Thread-safe.** Registration and a snapshot of matching handlers happen under
  an `RLock`, so handlers can subscribe or unsubscribe during delivery without
  corrupting an in-flight dispatch.

## Usage

```python
from app.events import event_bus, TransactionCreated

# Subscribe (returns an unsubscribe handle)
def notify(event: TransactionCreated) -> None:
    print("new transaction", event.transaction_id)

unsubscribe = event_bus.subscribe(TransactionCreated, notify)

# Or use the decorator form
@event_bus.on(TransactionCreated)
def audit(event: TransactionCreated) -> None:
    ...

# Publish
event_bus.publish(TransactionCreated(
    transaction_id="TXN-ABC123",
    account_number="**** 4521",
    amount=Decimal("100.00"),
    risk_score=10,
    risk_level="LOW",
    status="CLEARED",
    fraud_flags=["high_amount"],
))

unsubscribe()  # detach when done
```

## Integration

`app/main.py` attaches the default audit subscribers to the shared `event_bus`
at startup via `register_default_subscribers(event_bus)`. The transaction routes
publish on that bus:

- `POST /api/v1/transactions` publishes `TransactionCreated`, and additionally
  `TransactionHeld` when the transaction is auto-held.
- `POST /api/v1/transactions/{id}/review` publishes `TransactionReviewed`.

The built-in subscribers write structured lines to the `app.audit` logger. To
add behavior (for example a Slack notification or a metrics counter), write a
handler and subscribe it; no route code needs to change.

## Testing

- `tests/test_events.py` - unit tests for event validation/immutability and the
  full `EventBus` contract (ordering, de-duplication, isolation, unsubscribe,
  the `on` decorator, `clear`, thread safety, and the default subscribers).
- `tests/test_events_integration.py` - verifies the routes publish the expected
  events on the shared bus and that a failing subscriber never breaks a request.

For test isolation, create a fresh `EventBus()` rather than reusing the shared
singleton, or subscribe with the returned unsubscribe handle and detach in
teardown. `EventBus.clear()` also removes all subscriptions.
