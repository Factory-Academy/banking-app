import threading
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.events.bus import EventBus
from app.events.event_types import (
    Event,
    TransactionCreated,
    TransactionHeld,
    TransactionReviewed,
)


@pytest.fixture
def bus():
    return EventBus()


def _created(txn_id="TXN-1", status="HELD", score=85):
    return TransactionCreated(
        transaction_id=txn_id,
        account_number="**** 4521",
        amount=Decimal("15000.00"),
        risk_score=score,
        risk_level="HIGH",
        status=status,
        fraud_flags=["high_amount"],
    )


class TestSubscribeAndPublish:
    def test_handler_receives_published_event(self, bus):
        received = []
        bus.subscribe(TransactionCreated, received.append)

        event = _created()
        delivered = bus.publish(event)

        assert delivered == 1
        assert received == [event]

    def test_payload_is_preserved(self, bus):
        received = []
        bus.subscribe(TransactionCreated, received.append)

        bus.publish(_created(txn_id="TXN-99", score=42))

        assert received[0].transaction_id == "TXN-99"
        assert received[0].risk_score == 42
        assert received[0].amount == Decimal("15000.00")

    def test_multiple_handlers_all_invoked_in_order(self, bus):
        calls = []
        bus.subscribe(TransactionCreated, lambda e: calls.append("first"))
        bus.subscribe(TransactionCreated, lambda e: calls.append("second"))

        delivered = bus.publish(_created())

        assert delivered == 2
        assert calls == ["first", "second"]

    def test_publish_with_no_subscribers_returns_zero(self, bus):
        assert bus.publish(_created()) == 0

    def test_handler_only_receives_its_event_type(self, bus):
        created = []
        reviewed = []
        bus.subscribe(TransactionCreated, created.append)
        bus.subscribe(TransactionReviewed, reviewed.append)

        bus.publish(_created())

        assert len(created) == 1
        assert reviewed == []


class TestSubscriptionManagement:
    def test_duplicate_subscription_is_idempotent(self, bus):
        received = []
        handler = received.append
        bus.subscribe(TransactionCreated, handler)
        bus.subscribe(TransactionCreated, handler)

        bus.publish(_created())

        assert len(received) == 1
        assert bus.subscriber_count(TransactionCreated) == 1

    def test_unsubscribe_stops_delivery(self, bus):
        received = []
        handler = received.append
        bus.subscribe(TransactionCreated, handler)

        removed = bus.unsubscribe(TransactionCreated, handler)
        bus.publish(_created())

        assert removed is True
        assert received == []

    def test_unsubscribe_via_returned_handle(self, bus):
        received = []
        unsubscribe = bus.subscribe(TransactionCreated, received.append)

        unsubscribe()
        bus.publish(_created())

        assert received == []
        assert bus.subscriber_count(TransactionCreated) == 0

    def test_unsubscribe_unknown_handler_returns_false(self, bus):
        assert bus.unsubscribe(TransactionCreated, lambda e: None) is False

    def test_subscriber_count(self, bus):
        assert bus.subscriber_count(TransactionCreated) == 0
        bus.subscribe(TransactionCreated, lambda e: None)
        bus.subscribe(TransactionCreated, lambda e: None)
        assert bus.subscriber_count(TransactionCreated) == 2

    def test_clear_removes_all_subscriptions(self, bus):
        bus.subscribe(TransactionCreated, lambda e: None)
        bus.subscribe(TransactionReviewed, lambda e: None)

        bus.clear()

        assert bus.subscriber_count(TransactionCreated) == 0
        assert bus.subscriber_count(TransactionReviewed) == 0

    def test_on_decorator_registers_handler(self, bus):
        received = []

        @bus.on(TransactionCreated)
        def handler(event):
            received.append(event)

        bus.publish(_created())

        assert len(received) == 1
        # The decorator returns the original function unchanged.
        assert callable(handler)


class TestHierarchicalDispatch:
    def test_base_event_subscriber_receives_all_events(self, bus):
        received = []
        bus.subscribe(Event, received.append)

        bus.publish(_created())
        bus.publish(
            TransactionReviewed(
                transaction_id="TXN-1", decision="APPROVED", reviewed_by="Ann"
            )
        )
        bus.publish(
            TransactionHeld(
                transaction_id="TXN-1", account_number="**** 1", risk_score=90
            )
        )

        assert len(received) == 3

    def test_specific_and_base_subscribers_both_fire(self, bus):
        specific = []
        catch_all = []
        bus.subscribe(TransactionCreated, specific.append)
        bus.subscribe(Event, catch_all.append)

        bus.publish(_created())

        assert len(specific) == 1
        assert len(catch_all) == 1

    def test_base_subscriber_ignores_unrelated_hierarchy(self, bus):
        held = []
        bus.subscribe(TransactionHeld, held.append)

        # A TransactionCreated is not a TransactionHeld, so it must not match.
        bus.publish(_created())

        assert held == []


class TestErrorIsolation:
    def test_failing_handler_does_not_block_others(self, bus):
        received = []

        def boom(event):
            raise RuntimeError("handler failure")

        bus.subscribe(TransactionCreated, boom)
        bus.subscribe(TransactionCreated, received.append)

        delivered = bus.publish(_created())

        # The healthy handler still ran; the failing one is not counted.
        assert len(received) == 1
        assert delivered == 1

    def test_exception_is_logged(self, bus, caplog):
        def boom(event):
            raise ValueError("nope")

        bus.subscribe(TransactionCreated, boom)

        with caplog.at_level("ERROR"):
            bus.publish(_created())

        assert any("failed while handling" in rec.message for rec in caplog.records)


class TestConcurrencyAndMutation:
    def test_handler_can_unsubscribe_during_publish(self, bus):
        received = []

        def once(event):
            received.append(event)
            bus.unsubscribe(TransactionCreated, once)

        bus.subscribe(TransactionCreated, once)

        bus.publish(_created())
        bus.publish(_created())

        # Delivery uses a snapshot, so unsubscribing mid-dispatch is safe and
        # only affects subsequent publishes.
        assert len(received) == 1

    def test_concurrent_publish_is_thread_safe(self, bus):
        counter = {"n": 0}
        lock = threading.Lock()

        def handler(event):
            with lock:
                counter["n"] += 1

        bus.subscribe(TransactionCreated, handler)

        threads = [
            threading.Thread(target=lambda: bus.publish(_created()))
            for _ in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert counter["n"] == 20


class TestEventValueSemantics:
    def test_events_are_immutable(self):
        event = _created()
        with pytest.raises(FrozenInstanceError):
            event.transaction_id = "changed"

    def test_occurred_at_is_populated(self):
        event = _created()
        assert event.occurred_at is not None

    def test_optional_notes_defaults_to_none(self):
        event = TransactionReviewed(
            transaction_id="TXN-1", decision="APPROVED", reviewed_by="Ann"
        )
        assert event.notes is None
