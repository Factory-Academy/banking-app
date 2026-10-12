from typing import Optional


def normalize_transaction_id(transaction_id: Optional[str], include_prefix: bool = True) -> Optional[str]:
    """Normalize transaction ids for lookup."""
    if transaction_id is None:
        return None

    normalized = transaction_id.strip().upper()
    if not normalized:
        return None

    if not include_prefix and normalized.startswith("TXN-"):
        return normalized[4:]

    return normalized
