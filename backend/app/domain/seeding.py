from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class TransactionDraft:
    """A transaction to be created via the public API during seeding.

    Replaces the loose ``Dict[str, Any]`` that the seed generator built by hand.
    Keeping the draft typed means the JSON-encoding concerns (stringifying the
    amount, ISO-formatting the timestamp) live in one place: :meth:`to_api_payload`.
    """

    account_number: str
    account_holder_name: str
    amount: Decimal
    merchant_name: str
    merchant_category: str
    transaction_type: str
    location_city: str
    location_country: str
    latitude: Optional[float]
    longitude: Optional[float]
    timestamp: datetime

    def to_api_payload(self) -> Dict[str, Any]:
        """Render the draft as the JSON body expected by ``POST /transactions``."""
        return {
            "account_number": self.account_number,
            "account_holder_name": self.account_holder_name,
            "amount": str(self.amount),
            "merchant_name": self.merchant_name,
            "merchant_category": self.merchant_category,
            "transaction_type": self.transaction_type,
            "location_city": self.location_city,
            "location_country": self.location_country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": self.timestamp.isoformat(),
        }
