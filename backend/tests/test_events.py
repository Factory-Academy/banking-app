import logging
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
from app.events.subscribers import (
    log_transaction_held,
    register_default_subscribers,
)


@pytest.fixture
def bus():
    return EventBus()


def make_created(**overrides):
    kwargs = dict(
        transaction_id="TXN-1",
        account_number="**** 4521",
        amount=Decimal("100.00"),
        risk_score=10,
        risk_level="LOW",
        status="CLEARED",
        fraud_flags=["high_amount"],
    )
    kwargs.update(overrides)
    return TransactionCreated(**kwargs)


# ---------------------------------------------------------------------------
# Event value objects
# ---------------------------------------------------------------------------

class TestEventTypes:
    def test_created_event_holds_fields(self):
        event = make_created()
        assert event.transaction_id == "TXN-1"
        assert event.amount == Decimal("100.00")
        assert event.risk_score == 10

    def test_occurred_at_is_populated_automatically(self):
        event = make_created()
        assert event.occurred_at is not None

    def test_occurred_at_is_keyword_only(self):
        # It must not be assignable as a trailing positional argument.
        with pytest.raises(TypeError):
            TransactionReviewed("TXN-1", "APPROVED", "analyst", None, "2020-01-01")

    def test_events_are_immutable(self):
        event = make_created()
        with pytest.raises(FrozenInstanceError):
            event.transaction_id = "TXN-999"

    def test_fraud_flags_are_frozen_to_a_tuple(self):
        event = make_created(fraud_flags=["a", "b"])
        assert event.fraud_flags == ("a", "b")
        assert isinstance(event.fraud_flags, tuple)

    def test_fraud_flags_are_copied_from_the_source_list(self):
        source = ["high_amount"]
        event = make_created(fraud_flags=source)
        source.append("mutated")
        assert event.fraud_flags == ("high_amount",)

    def test_empty_fraud_flags_default(self):
        event = TransactionHeld(
            transaction_id="TXN-1",
            account_number="**** 4521",
            risk_score=80,
        )
        assert event.fraud_flags == ()

    @pytest.mark.parametrize("bad", ["", "   ", None, 123])
    def test_blank_transaction_id_is_rejected(self, bad):
        with pytest.raises(ValueError):
            make_created(transaction_id=bad)

    def test_blank_account_number_is_rejected(self):
        with pytest.raises(ValueError):
            make_created(account_number="  ")

    @pytest.mark.parametrize("bad", [-1, "10", 3.5, True])
    def test_negative_or_non_int_risk_score_is_rejected(self, bad):
        with pytest.raises(ValueError):
            make_created(risk_score=bad)

    def test_zero_risk_score_is_allowed(self):
        assert make_created(risk_score=0).risk_score == 0

    def test_reviewed_requires_decision_and_reviewer(self):
        with pytest.raises(ValueError):
            TransactionReviewed(transaction_id="TXN-1", decision="", reviewed_by="a")
        with pytest.raises(ValueError):
            TransactionReviewed(transaction_id="TXN-1", decision="APPROVED", reviewed_by=" ")

    def test_reviewed_notes_are_optional(self):
        event = TransactionReviewed(
            transaction_id="TXN-1", decision="APPROVED", reviewed_by="analyst"
        )
        assert event.notes is None


# ---------------------------------------------------------------------------
# EventBus dispatch
# ---------------------------------------------------------------------------

class TestEventBus:
    def test_subscribe_and_publish_delivers(self, bus):
        received = []
        bus.subscribe(TransactionCreated, received.append)
        bus.publish(make_created())
        assert len(received) == 1

    def test_publish_returns_delivered_count(self, bus):
        bus.subscribe(TransactionCreated, lambda e: None)
        bus.subscribe(TransactionCreated, lambda e: None)
        assert bus.publish(make_created()) == 2

    def test_handlers_invoked_in_registration_order(self, bus):
        order = []
        bus.subscribe(TransactionCreated, lambda e: order.append("first"))
        bus.subscribe(TransactionCreated, lambda e: order.append("second"))
        bus.publish(make_created())
        assert order == ["first", "second"]

    def test_duplicate_subscribe_is_a_noop(self, bus):
        received = []
        handler = received.append
        bus.subscribe(TransactionCreated, handler)
        bus.subscribe(TransactionCreated, handler)
        assert bus.subscriber_count(TransactionCreated) == 1
        bus.publish(make_created())
        assert len(received) == 1

    def test_handlers_only_receive_their_event_type(self, bus):
        created, held = [], []
        bus.subscribe(TransactionCreated, created.append)
        bus.subscribe(TransactionHeld, held.append)
        bus.publish(make_created())
        assert len(created) == 1 and held == []

    def test_subscribing_to_base_event_is_catch_all(self, bus):
        seen = []
        bus.subscribe(Event, seen.append)
        bus.publish(make_created())
        bus.publish(TransactionHeld(
            transaction_id="TXN-2", account_number="x", risk_score=80
        ))
        assert len(seen) == 2

    def test_handler_on_both_class_and_base_runs_once(self, bus):
        count = []
        handler = lambda e: count.append(1)
        bus.subscribe(Event, handler)
        bus.subscribe(TransactionCreated, handler)
        delivered = bus.publish(make_created())
        assert len(count) == 1
        assert delivered == 1

    def test_failing_handler_is_isolated(self, bus, caplog):
        survivor = []

        def boom(event):
            raise RuntimeError("handler blew up")

        bus.subscribe(TransactionCreated, boom)
        bus.subscribe(TransactionCreated, survivor.append)
        with caplog.at_level(logging.ERROR):
            delivered = bus.publish(make_created())
        assert len(survivor) == 1
        assert delivered == 1
        assert "failed while handling" in caplog.text

    def test_unsubscribe_returns_true_when_removed(self, bus):
        handler = lambda e: None
        bus.subscribe(TransactionCreated, handler)
        assert bus.unsubscribe(TransactionCreated, handler) is True
        assert bus.subscriber_count(TransactionCreated) == 0

    def test_unsubscribe_returns_false_when_absent(self, bus):
        assert bus.unsubscribe(TransactionCreated, lambda e: None) is False

    def test_subscribe_returns_working_unsubscribe_handle(self, bus):
        received = []
        unsubscribe = bus.subscribe(TransactionCreated, received.append)
        unsubscribe()
        bus.publish(make_created())
        assert received == []

    def test_on_decorator_registers_and_returns_function(self, bus):
        received = []

        @bus.on(TransactionCreated)
        def handler(event):
            received.append(event)

        bus.publish(make_created())
        assert len(received) == 1
        # The decorated function is returned unchanged and still callable.
        handler(make_created())
        assert len(received) == 2

    def test_clear_all(self, bus):
        bus.subscribe(TransactionCreated, lambda e: None)
        bus.subscribe(TransactionHeld, lambda e: None)
        bus.clear()
        assert bus.subscriber_count(TransactionCreated) == 0
        assert bus.subscriber_count(TransactionHeld) == 0

    def test_clear_single_type_leaves_others(self, bus):
        bus.subscribe(TransactionCreated, lambda e: None)
        bus.subscribe(TransactionHeld, lambda e: None)
        bus.clear(TransactionCreated)
        assert bus.subscriber_count(TransactionCreated) == 0
        assert bus.subscriber_count(TransactionHeld) == 1

    def test_subscriber_count_counts_exact_type_only(self, bus):
        bus.subscribe(Event, lambda e: None)
        assert bus.subscriber_count(TransactionCreated) == 0
        assert bus.subscriber_count(Event) == 1

    def test_subscribe_rejects_non_event_type(self, bus):
        with pytest.raises(TypeError):
            bus.subscribe(str, lambda e: None)

    def test_subscribe_rejects_non_callable(self, bus):
        with pytest.raises(TypeError):
            bus.subscribe(TransactionCreated, "not callable")

    def test_publish_rejects_non_event(self, bus):
        with pytest.raises(TypeError):
            bus.publish({"transaction_id": "TXN-1"})

    def test_unsubscribe_during_publish_does_not_affect_current_dispatch(self, bus):
        calls = []

        def first(event):
            calls.append("first")
            bus.unsubscribe(TransactionCreated, second)

        def second(event):
            calls.append("second")

        bus.subscribe(TransactionCreated, first)
        bus.subscribe(TransactionCreated, second)
        # The snapshot is taken before dispatch, so ``second`` still runs this
        # time even though ``first`` removed it.
        bus.publish(make_created())
        assert calls == ["first", "second"]
        calls.clear()
        bus.publish(make_created())
        assert calls == ["first"]

    def test_concurrent_subscribe_is_thread_safe(self, bus):
        def worker(n):
            bus.subscribe(TransactionCreated, lambda e, n=n: None)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert bus.subscriber_count(TransactionCreated) == 50


# ---------------------------------------------------------------------------
# Default audit subscribers
# ---------------------------------------------------------------------------

class TestDefaultSubscribers:
    def test_register_attaches_three_subscribers(self, bus):
        register_default_subscribers(bus)
        assert bus.subscriber_count(TransactionCreated) == 1
        assert bus.subscriber_count(TransactionHeld) == 1
        assert bus.subscriber_count(TransactionReviewed) == 1

    def test_register_returns_unsubscribe_handles(self, bus):
        handles = register_default_subscribers(bus)
        assert len(handles) == 3
        for unsubscribe in handles:
            unsubscribe()
        assert bus.subscriber_count(TransactionCreated) == 0

    def test_created_subscriber_logs_info(self, bus, caplog):
        register_default_subscribers(bus)
        with caplog.at_level(logging.INFO, logger="app.audit"):
            bus.publish(make_created())
        assert "transaction_created id=TXN-1" in caplog.text

    def test_held_subscriber_logs_warning_with_flags(self, bus, caplog):
        register_default_subscribers(bus)
        with caplog.at_level(logging.WARNING, logger="app.audit"):
            bus.publish(TransactionHeld(
                transaction_id="TXN-5",
                account_number="**** 1111",
                risk_score=90,
                fraud_flags=["high_amount", "velocity"],
            ))
        assert "transaction_held id=TXN-5" in caplog.text
        assert "flags=high_amount,velocity" in caplog.text

    def test_held_subscriber_renders_none_for_empty_flags(self, caplog):
        with caplog.at_level(logging.WARNING, logger="app.audit"):
            log_transaction_held(TransactionHeld(
                transaction_id="TXN-6", account_number="x", risk_score=70
            ))
        assert "flags=none" in caplog.text
