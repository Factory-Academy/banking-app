"""Fraud detection rules.

Each rule is a thin, defensive wrapper around the pure helpers in this package.
Rules never raise on malformed input: a field they cannot interpret simply means
the rule does not fire, which keeps a single bad record from blocking the whole
assessment.
"""

from abc import ABC, abstractmethod
from datetime import timedelta
from decimal import Decimal
from typing import List

from app.models.transaction import Transaction
from app.utils.cache import ttl_cache

from .geo import distance_between, haversine_distance
from .normalization import (
    HOME_COUNTRY,
    is_home_country,
    normalize_country,
    safe_decimal,
    safe_timestamp,
)
from .scoring import average_amount
from .windows import iter_history, transactions_within

HIGH_AMOUNT_THRESHOLD = Decimal("10000")
VELOCITY_WINDOW = timedelta(hours=1)
VELOCITY_MAX_TRANSACTIONS = 5
GEO_WINDOW = timedelta(hours=4)
GEO_DISTANCE_THRESHOLD_KM = 500
UNUSUAL_HOUR_START = 2
UNUSUAL_HOUR_END = 5
AMOUNT_DEVIATION_MULTIPLE = 3
AMOUNT_DEVIATION_MIN_HISTORY = 3


class FraudRule(ABC):
    """Base class for fraud detection rules"""

    def __init__(self, name: str, risk_points: int):
        self.name = name
        self.risk_points = risk_points

    @abstractmethod
    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        """Returns True if rule is triggered"""
        raise NotImplementedError


class HighAmountRule(FraudRule):
    """Flag transactions over $10,000"""

    def __init__(self):
        super().__init__("high_amount", 30)

    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        amount = safe_decimal(getattr(transaction, "amount", None))
        if amount is None:
            return False
        return amount > HIGH_AMOUNT_THRESHOLD


class VelocityRule(FraudRule):
    """Flag more than 5 transactions within 1 hour"""

    def __init__(self):
        super().__init__("high_velocity", 40)

    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        reference = safe_timestamp(getattr(transaction, "timestamp", None))
        if reference is None:
            return False
        recent = transactions_within(
            iter_history(account_history),
            reference,
            VELOCITY_WINDOW,
            inclusive_end=True,
        )
        return len(recent) > VELOCITY_MAX_TRANSACTIONS


class GeographicAnomalyRule(FraudRule):
    """Flag transactions in different country within 4 hours"""

    def __init__(self):
        super().__init__("geographic_anomaly", 50)

    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        reference = safe_timestamp(getattr(transaction, "timestamp", None))
        if reference is None:
            return False

        current_country = normalize_country(getattr(transaction, "location_country", None))
        recent = transactions_within(
            iter_history(account_history),
            reference,
            GEO_WINDOW,
            inclusive_end=False,
        )

        for prev_txn in recent:
            prev_country = normalize_country(getattr(prev_txn, "location_country", None))
            if prev_country == current_country:
                continue

            distance = self._calculate_distance(
                getattr(prev_txn, "latitude", None),
                getattr(prev_txn, "longitude", None),
                getattr(transaction, "latitude", None),
                getattr(transaction, "longitude", None),
            )
            if distance is None:
                # Different country but no usable coordinates: flag on country alone.
                return True
            if distance > GEO_DISTANCE_THRESHOLD_KM:
                return True
        return False

    @staticmethod
    @ttl_cache(ttl=3600, maxsize=1000)
    def _calculate_distance(lat1, lon1, lat2, lon2):
        """Cached distance in km, or ``None`` when coordinates are unusable."""
        return distance_between(lat1, lon1, lat2, lon2)


class UnusualTimeRule(FraudRule):
    """Flag transactions between 2 AM - 5 AM local time"""

    def __init__(self):
        super().__init__("unusual_time", 20)

    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        ts = safe_timestamp(getattr(transaction, "timestamp", None))
        if ts is None:
            return False
        return UNUSUAL_HOUR_START <= ts.hour < UNUSUAL_HOUR_END


class FirstInternationalRule(FraudRule):
    """Flag first international transaction for account"""

    def __init__(self):
        super().__init__("first_international", 25)

    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        if is_home_country(getattr(transaction, "location_country", None)):
            return False

        for prev_txn in iter_history(account_history):
            if not is_home_country(getattr(prev_txn, "location_country", None)):
                return False
        return True


class AmountDeviationRule(FraudRule):
    """Flag transactions >3x the account's average"""

    def __init__(self):
        super().__init__("amount_deviation", 35)

    def evaluate(self, transaction: Transaction, account_history: List[Transaction]) -> bool:
        current = safe_decimal(getattr(transaction, "amount", None))
        if current is None:
            return False

        history = iter_history(account_history)
        valid_amounts = [
            d
            for d in (safe_decimal(getattr(t, "amount", None)) for t in history)
            if d is not None
        ]
        if len(valid_amounts) < AMOUNT_DEVIATION_MIN_HISTORY:
            return False

        avg = average_amount(valid_amounts)
        if avg is None or avg <= 0:
            return False
        return current > (avg * AMOUNT_DEVIATION_MULTIPLE)


__all__ = [
    "FraudRule",
    "HighAmountRule",
    "VelocityRule",
    "GeographicAnomalyRule",
    "UnusualTimeRule",
    "FirstInternationalRule",
    "AmountDeviationRule",
    "haversine_distance",
    "HOME_COUNTRY",
]
