from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from app.events.event_types import (
    TransactionCreated,
    TransactionHeld,
    TransactionReviewed,
)


def _created(**overrides):
    payload = {
        "transaction_id": "TXN-1",
        "account_number": "**** 4521",
        "amount": Decimal("15000.00"),
        "risk_score": 85,
        "risk_level": "HIGH",
        "status": "HELD",
        "fraud_flags": ["high_amount"],
    }
    payload.update(overrides)
    return TransactionCreated(**payload)


class TestFlagNormalization:
    def test_list_flags_become_a_tuple(self):
        event = _created(fraud_flags=["a", "b"])
        assert event.fraud_flags == ("a", "b")
        assert isinstance(event.fraud_flags, tuple)

    def test_default_flags_is_empty_tuple(self):
        event = _created(fraud_flags=())
        assert event.fraud_flags == ()

    def test_none_flags_normalizes_to_empty_tuple(self):
        # The route builds flags with ``list(value or [])``; guard against a
        # caller that still slips a ``None`` through.
        event = TransactionHeld(
            transaction_id="TXN-1",
            account_number="**** 1",
            risk_score=90,
            fraud_flags=None,
        )
        assert event.fraud_flags == ()

    def test_mutating_source_does_not_affect_event(self):
        source = ["high_amount"]
        event = _created(fraud_flags=source)
        source.append("velocity")
        assert event.fraud_flags == ("high_amount",)


class TestIdentifierValidation:
    @pytest.mark.parametrize("bad_id", ["", "   ", None])
    def test_created_rejects_blank_transaction_id(self, bad_id):
        with pytest.raises(ValueError):
            _created(transaction_id=bad_id)

    def test_created_rejects_blank_account_number(self):
        with pytest.raises(ValueError):
            _created(account_number="")

    def test_held_rejects_blank_transaction_id(self):
        with pytest.raises(ValueError):
            TransactionHeld(
                transaction_id="  ", account_number="**** 1", risk_score=90
            )

    def test_reviewed_rejects_blank_decision(self):
        with pytest.raises(ValueError):
            TransactionReviewed(
                transaction_id="TXN-1", decision="", reviewed_by="Ann"
            )

    def test_reviewed_rejects_blank_reviewer(self):
        with pytest.raises(ValueError):
            TransactionReviewed(
                transaction_id="TXN-1", decision="APPROVED", reviewed_by="   "
            )


class TestScoreValidation:
    def test_negative_risk_score_is_rejected(self):
        with pytest.raises(ValueError):
            _created(risk_score=-1)

    def test_zero_risk_score_is_allowed(self):
        assert _created(risk_score=0).risk_score == 0

    def test_negative_held_score_is_rejected(self):
        with pytest.raises(ValueError):
            TransactionHeld(
                transaction_id="TXN-1", account_number="**** 1", risk_score=-5
            )


class TestImmutability:
    def test_cannot_reassign_field(self):
        event = _created()
        with pytest.raises(FrozenInstanceError):
            event.transaction_id = "changed"

    def test_occurred_at_is_populated(self):
        assert _created().occurred_at is not None

    def test_reviewed_notes_default_to_none(self):
        event = TransactionReviewed(
            transaction_id="TXN-1", decision="APPROVED", reviewed_by="Ann"
        )
        assert event.notes is None
