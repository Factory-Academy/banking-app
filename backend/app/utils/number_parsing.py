"""Helpers for parsing numeric values used by validation utilities."""
from decimal import Decimal, InvalidOperation
from typing import Any


class NumericParsingError(Exception):
    """Raised when a value cannot be parsed as a Decimal."""

    def __init__(self, field_name: str, value: Any):
        self.field_name = field_name
        self.value = value
        self.message = (
            f"{field_name} must be a valid number, got {type(value).__name__}"
        )
        super().__init__(self.message)


def parse_decimal_value(value: Any, field_name: str) -> Decimal:
    """
    Parse a value as Decimal.

    Raises:
        NumericParsingError: If the value cannot be parsed as Decimal
    """
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation):
        raise NumericParsingError(field_name=field_name, value=value)
