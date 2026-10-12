class TransactionNotFoundError(Exception):
    """Raised when a requested transaction does not exist."""

    def __init__(self, transaction_id: str):
        super().__init__("Transaction not found")
        self.transaction_id = transaction_id


class RateLimitExceededError(Exception):
    """Raised when a client exceeds its allowed request rate."""

    def __init__(self, key: str, retry_after: float):
        super().__init__("Rate limit exceeded")
        self.key = key
        self.retry_after = retry_after
