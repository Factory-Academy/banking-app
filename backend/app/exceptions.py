class TransactionNotFoundError(Exception):
    """Raised when a requested transaction does not exist."""

    def __init__(self, transaction_id: str):
        super().__init__("Transaction not found")
        self.transaction_id = transaction_id
