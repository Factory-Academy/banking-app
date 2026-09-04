"""Unit tests for the in-process pub/sub event bus."""
import threading
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.events.bus import EventBus
from app.events.event_types import (
    DomainEvent,
    TransactionCreated,
    TransactionHeld,
    TransactionReviewed,
)


@pytest.fixture
def bus():
    return EventBus()


def make_created(**overrides):
    defaults = dict(
        transaction_id="TXN-1",
        account_number="**** 0001",
        amount=Decimal("100.00"),
        risk_score=10,
        risk_level="LOW",
        status="CLEARED",
        fraud_flags=[],
    )
    defaults.update(overrides)
    return TransactionCreated(**defaults)


class TestEventTypes:
    def test_occurred_at_defaults_to_aware_utc(self):
        event = make_created()
        assert event.occurred_at.tzinfo is not None
        assert event.occurred_at.tzinfo == timezone.utc

    def test_occurred_at_can_be_supplied(self):
        moment = datetime(2020, 1, 1, tzinfo=timezone.utc)
        event = make_created(occurred_at=moment)
        assert event.occurred_at == moment

    def test_event_name_is_class_name(self):
        assert make_created().name == "TransactionCreated"

    def test_events_are_frozen(self):
        event = make_created()
        with pytest.raises(Exception):
            event.transaction_id = "changed"  # type: ignore[misc]

    def test_default_flags_are_independent(self):
        a = make_created()
        b = make_created()
        assert a.fraud_flags == [] and b.fraud_flags == []
        assert a.fraud_flags is not b.fraud_flags


class TestSubscribeAndPublish:
    def test_handler_receives_published_event(self, bus):
        received = []
        bus.subscribe(TransactionCreated, received.append)
        event = make_created()

        result = bus.publish(event)

        assert received == [event]
        assert result.handled == 1
        assert result.ok

    def test_handlers_fire_in_subscription_order(self, bus):
        order = []
        bus.subscribe(TransactionCreated, lambda e: order.append("first"))
        bus.subscribe(TransactionCreated, lambda e: order.append("second"))
        bus.subscribe(TransactionCreated, lambda e: order.append("third"))

        bus.publish(make_created())

        assert order == ["first", "second", "third"]

    def test_dispatch_is_type_scoped(self, bus):
        created, reviewed = [], []
        bus.subscribe(TransactionCreated, created.append)
        bus.subscribe(TransactionReviewed, reviewed.append)

        bus.publish(make_created())

        assert len(created) == 1
        assert reviewed == []

    def test_publish_with_no_subscribers_is_noop(self, bus):
        result = bus.publish(make_created())
        assert result.handled == 0
        assert result.ok

    def test_publish_rejects_non_event(self, bus):
        with pytest.raises(TypeError):
            bus.publish("not-an-event")  # type: ignore[arg-type]

    def test_subscribe_rejects_non_event_type(self, bus):
        with pytest.raises(TypeError):
            bus.subscribe(str, lambda e: None)  # type: ignore[arg-type]

    def test_subscribe_rejects_non_callable(self, bus):
        with pytest.raises(TypeError):
            bus.subscribe(TransactionCreated, 123)  # type: ignore[arg-type]


class TestBaseClassDispatch:
    def test_subscribe_all_receives_every_event(self, bus):
        seen = []
        bus.subscribe_all(seen.append)

        bus.publish(make_created())
        bus.publish(TransactionReviewed(
            transaction_id="TXN-1",
            account_number="**** 0001",
            decision="APPROVED",
            reviewed_by="Analyst",
            previous_status="HELD",
        ))

        assert len(seen) == 2

    def test_exact_type_handlers_run_before_base_handlers(self, bus):
        order = []
        bus.subscribe_all(lambda e: order.append("all"))
        bus.subscribe(TransactionCreated, lambda e: order.append("exact"))

        bus.publish(make_created())

        assert order == ["exact", "all"]


class TestUnsubscribe:
    def test_unsubscribe_stops_delivery(self, bus):
        received = []
        sub = bus.subscribe(TransactionCreated, received.append)

        bus.publish(make_created())
        sub.unsubscribe()
        bus.publish(make_created())

        assert len(received) == 1
        assert sub.active is False

    def test_unsubscribe_is_idempotent(self, bus):
        sub = bus.subscribe(TransactionCreated, lambda e: None)
        sub.unsubscribe()
        sub.unsubscribe()  # must not raise
        assert bus.subscriber_count() == 0

    def test_subscriber_count_tracks_active_subscriptions(self, bus):
        assert bus.subscriber_count() == 0
        s1 = bus.subscribe(TransactionCreated, lambda e: None)
        bus.subscribe(TransactionReviewed, lambda e: None)
        assert bus.subscriber_count() == 2
        assert bus.subscriber_count(TransactionCreated) == 1
        s1.unsubscribe()
        assert bus.subscriber_count() == 1
        assert bus.subscriber_count(TransactionCreated) == 0

    def test_clear_all(self, bus):
        s1 = bus.subscribe(TransactionCreated, lambda e: None)
        s2 = bus.subscribe(TransactionReviewed, lambda e: None)
        bus.clear()
        assert bus.subscriber_count() == 0
        assert not s1.active and not s2.active

    def test_clear_single_type(self, bus):
        bus.subscribe(TransactionCreated, lambda e: None)
        bus.subscribe(TransactionReviewed, lambda e: None)
        bus.clear(TransactionCreated)
        assert bus.subscriber_count(TransactionCreated) == 0
        assert bus.subscriber_count(TransactionReviewed) == 1


class TestOnceSubscriptions:
    def test_once_handler_fires_exactly_once(self, bus):
        received = []
        bus.subscribe(TransactionCreated, received.append, once=True)

        bus.publish(make_created())
        bus.publish(make_created())

        assert len(received) == 1
        assert bus.subscriber_count() == 0

    def test_once_via_subscribe_all(self, bus):
        received = []
        bus.subscribe_all(received.append, once=True)
        bus.publish(make_created())
        bus.publish(make_created())
        assert len(received) == 1


class TestErrorIsolation:
    def test_failing_handler_does_not_block_others(self, bus):
        received = []

        def boom(event):
            raise RuntimeError("handler exploded")

        bus.subscribe(TransactionCreated, boom)
        bus.subscribe(TransactionCreated, received.append)

        result = bus.publish(make_created())

        assert len(received) == 1
        assert result.handled == 1
        assert not result.ok
        assert len(result.errors) == 1
        assert isinstance(result.errors[0].exception, RuntimeError)

    def test_raise_on_error_propagates(self):
        strict_bus = EventBus(raise_on_error=True)

        def boom(event):
            raise ValueError("nope")

        strict_bus.subscribe(TransactionCreated, boom)

        with pytest.raises(ValueError):
            strict_bus.publish(make_created())

    def test_once_handler_cleaned_up_even_when_it_raises(self, bus):
        def boom(event):
            raise RuntimeError("boom")

        bus.subscribe(TransactionCreated, boom, once=True)
        result = bus.publish(make_created())

        assert not result.ok
        assert bus.subscriber_count() == 0


class TestDispatchStability:
    def test_handler_subscribing_during_publish_is_not_notified_same_round(self, bus):
        late = []

        def subscriber(event):
            bus.subscribe(TransactionCreated, late.append)

        bus.subscribe(TransactionCreated, subscriber)
        bus.publish(make_created())

        # The handler added mid-dispatch must not see the in-flight event.
        assert late == []
        # ...but it is registered for the next publish.
        bus.publish(make_created())
        assert len(late) == 1

    def test_handler_unsubscribing_another_mid_dispatch(self, bus):
        received = []
        second = bus.subscribe(TransactionCreated, received.append)

        def canceller(event):
            second.unsubscribe()

        # Register canceller before ``second`` in the dispatch order by
        # clearing and re-adding in the intended sequence.
        bus.clear()
        bus.subscribe(TransactionCreated, canceller)
        second = bus.subscribe(TransactionCreated, received.append)

        bus.publish(make_created())
        # ``second`` was cancelled before its turn, so it should not fire.
        assert received == []


class TestThreadSafety:
    def test_concurrent_publish_is_safe(self, bus):
        counter = {"n": 0}
        lock = threading.Lock()

        def handler(event):
            with lock:
                counter["n"] += 1

        bus.subscribe(TransactionCreated, handler)

        def worker():
            for _ in range(100):
                bus.publish(make_created())

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter["n"] == 8 * 100

    def test_concurrent_subscribe_unsubscribe(self, bus):
        def worker():
            for _ in range(200):
                sub = bus.subscribe(TransactionHeld, lambda e: None)
                sub.unsubscribe()

        threads = [threading.Thread(target=worker) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert bus.subscriber_count() == 0
