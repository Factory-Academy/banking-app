# In-Process Event Bus

A small, dependency-free publish/subscribe layer that lets parts of the backend
react to domain events (a transaction created, held, or reviewed) without the
publisher knowing who is listening.

It lives in `backend/app/events/`:

| File | Purpose |
| --- | --- |
| `event_types.py` | Typed, immutable event classes (`DomainEvent` + subclasses). |
| `bus.py` | The `EventBus`, `Subscription`, `PublishResult`, and the shared `event_bus` instance. |
| `subscribers.py` | Built-in audit-logging handlers + `register_default_subscribers`. |
| `__init__.py` | Public exports. |

## Why

The transaction routes previously did their work and returned. Anything else
that needed to know about a transaction (audit logging, notifications, metrics)
would have to be bolted directly into the route. The bus decouples that: the
route publishes a typed event and any number of subscribers react, each in
isolation.

## Events

All events derive from `DomainEvent` and are frozen dataclasses, so a published
event is an immutable record. Every event carries an `occurred_at` timestamp
(timezone-aware UTC) and exposes a `name` property.

- `TransactionCreated` - emitted for every accepted transaction.
- `TransactionHeld` - emitted additionally when a transaction is auto-held (HIGH risk).
- `TransactionReviewed` - emitted when an analyst approves/rejects/escalates.

## Usage

### Subscribe

```python
from app.events import event_bus, TransactionHeld

def alert_on_hold(event: TransactionHeld) -> None:
    print(f"Held {event.transaction_id} for ${event.amount} (score {event.risk_score})")

subscription = event_bus.subscribe(TransactionHeld, alert_on_hold)
```

Subscribe to a base class to receive everything:

```python
from app.events import DomainEvent

event_bus.subscribe(DomainEvent, lambda e: print(e.name))
# or the convenience wrapper:
event_bus.subscribe_all(lambda e: print(e.name))
```

Fire a handler only once:

```python
event_bus.subscribe(TransactionHeld, handler, once=True)
```

### Publish

```python
from app.events import event_bus, TransactionCreated
from decimal import Decimal

result = event_bus.publish(TransactionCreated(
    transaction_id="TXN-ABC123",
    account_number="**** 1234",
    amount=Decimal("100.00"),
    risk_score=10,
    risk_level="LOW",
    status="CLEARED",
    fraud_flags=[],
))

print(result.handled)  # number of handlers that ran successfully
print(result.ok)       # False if any handler raised
print(result.errors)   # list of HandlerError(subscription, exception)
```

### Unsubscribe

```python
subscription.unsubscribe()   # idempotent
event_bus.clear(TransactionHeld)  # drop all handlers for one event type
event_bus.clear()                 # drop everything
```

## Semantics

- **Typed dispatch.** Subscriptions are keyed on the event class. Publishing
  walks the event's MRO, so exact-type handlers run first, then base-class
  handlers (including `subscribe_all`). Handlers run in subscription order.
- **Error isolation.** By default a handler that raises is logged and recorded
  on `PublishResult.errors`; the remaining handlers still run. Create
  `EventBus(raise_on_error=True)` to make failures propagate instead.
- **Stable dispatch.** The set of handlers is snapshotted at publish time, so a
  handler that subscribes or unsubscribes mid-dispatch does not affect the
  round in flight.
- **Thread-safe.** Subscribe, unsubscribe, and publish are guarded by a
  reentrant lock and are safe to call from multiple threads.
- **In-process only.** This is not a message queue. Delivery is synchronous and
  scoped to the running process; there is no persistence or retry.

## Integration points

`app/routes/transactions.py` publishes on the shared `event_bus`:

- `POST /api/v1/transactions` -> `TransactionCreated` (plus `TransactionHeld`
  when the transaction is auto-held).
- `POST /api/v1/transactions/{id}/review` -> `TransactionReviewed`.

`app/main.py` calls `register_default_subscribers(event_bus)` at startup to
attach the audit-logging handlers in `subscribers.py`.

## Tests

- `backend/tests/test_events.py` - bus unit tests (dispatch, ordering, base-class
  dispatch, unsubscribe, `once`, error isolation, mid-dispatch stability, thread
  safety).
- `backend/tests/test_events_integration.py` - verifies the API publishes the
  expected events and that a failing subscriber cannot break a request.

Run just these:

```bash
cd backend
pytest tests/test_events.py tests/test_events_integration.py
```
