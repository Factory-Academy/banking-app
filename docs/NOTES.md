# In-Process Event Bus

A lightweight, synchronous publish/subscribe module for decoupling side
effects (audit logging, alerting, notifications) from the request handlers that
drive the core transaction flow. It lives entirely in-process with no external
broker, no threads of its own, and no new dependencies.

Source: `backend/app/events/`

- `event_types.py` – immutable, typed event definitions
- `bus.py` – the `EventBus` and the process-wide `event_bus` singleton
- `subscribers.py` – built-in audit subscribers and `register_default_subscribers`

## Events

Events are frozen dataclasses that describe something that already happened.
They all inherit from `Event`, which stamps an `occurred_at` timestamp. Payloads
carry plain values (ids, amounts, flags) rather than ORM objects, so a
subscriber never touches a database session it does not own.

| Event | Published when | Key fields |
| --- | --- | --- |
| `TransactionCreated` | a transaction is created and scored | `transaction_id`, `account_number`, `amount`, `risk_score`, `risk_level`, `status`, `fraud_flags` |
| `TransactionHeld` | a new transaction scores HIGH and is auto-held | `transaction_id`, `account_number`, `risk_score`, `fraud_flags` |
| `TransactionReviewed` | an analyst approves / rejects / escalates a held txn | `transaction_id`, `decision`, `reviewed_by`, `notes` |

## Subscribing

```python
from app.events import event_bus, TransactionHeld

def alert_on_hold(event: TransactionHeld) -> None:
    print(f"HELD {event.transaction_id} scored {event.risk_score}")

# subscribe() returns a handle that detaches the subscription
unsubscribe = event_bus.subscribe(TransactionHeld, alert_on_hold)
...
unsubscribe()
```

The decorator form is equivalent:

```python
@event_bus.on(TransactionHeld)
def alert_on_hold(event: TransactionHeld) -> None:
    ...
```

Subscribing to the base `Event` type is a catch-all: dispatch walks the event's
class hierarchy, so a handler registered for `Event` receives every event on the
bus. This is how the integration tests observe the full stream.

## Publishing

```python
from app.events import event_bus, TransactionReviewed

delivered = event_bus.publish(
    TransactionReviewed(
        transaction_id="TXN-ABC123",
        decision="REJECTED",
        reviewed_by="Sarah Johnson",
        notes="Confirmed fraud",
    )
)
```

`publish` invokes matching handlers synchronously in registration order and
returns the number that completed without raising.

## Guarantees and edge cases

- **Error isolation** – if a handler raises, the exception is logged to the
  `app.audit` logger and the remaining handlers still run. One broken
  subscriber cannot break the flow that published the event.
- **Idempotent subscribe** – registering the same handler for the same event
  type twice is a no-op; it will not receive duplicate deliveries.
- **At most once per publish across the hierarchy** – dispatch walks the
  event's MRO, but a handler registered for both a class and one of its bases
  (for example both `TransactionCreated` and the catch-all `Event`) is invoked
  only once per publish. Handlers still run most-specific-type first.
- **Safe mutation during dispatch** – handlers are delivered from a snapshot,
  so a handler may subscribe or unsubscribe while an event is being published.
  Such changes only affect later publishes.
- **Thread-safe** – all registry access is guarded by a re-entrant lock, which
  matters because FastAPI may serve requests on multiple worker threads.
- **Immutable events** – events are frozen dataclasses, and list-valued
  payloads such as `fraud_flags` are copied into a tuple on construction, so a
  subscriber cannot mutate an event (or the list a publisher handed in) and
  affect another subscriber.
- **Fail-fast validation** – the bus rejects a non-`Event` type or a
  non-callable handler with `TypeError`, and `publish` rejects a non-`Event`
  argument. Events themselves reject blank identifiers and negative risk
  scores with `ValueError`, surfacing publisher bugs at the call site instead
  of inside a subscriber.
- **Targeted teardown** – `clear()` removes every subscription, while
  `clear(EventType)` removes only the handlers registered for that exact type.

## Integration points

The transaction routes (`app/routes/transactions.py`) publish after the
database commit succeeds:

- `POST /api/v1/transactions` → `TransactionCreated`, plus `TransactionHeld`
  when the transaction is auto-held.
- `POST /api/v1/transactions/{id}/review` → `TransactionReviewed`.

The default audit subscribers are wired onto `event_bus` at app startup in
`app/main.py` via `register_default_subscribers`.

## Testing

- `tests/test_event_bus.py` – unit coverage for the bus itself (dispatch,
  subscription management, hierarchy, error isolation, concurrency, event value
  semantics).
- `tests/test_events_integration.py` – verifies the API flow publishes the
  expected events, using a catch-all subscriber on the shared `event_bus`.

```bash
cd backend
pytest tests/test_event_bus.py tests/test_events_integration.py
```
