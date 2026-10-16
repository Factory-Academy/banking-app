"""
Lightweight request/response validation utilities.

Provides reusable validation functions and decorators for common validation patterns
across API endpoints. Designed to complement Pydantic's schema validation with
business logic and custom constraints.
"""
from typing import Any, Callable, Optional, List, TypeVar, Union
from decimal import Decimal
from datetime import datetime
from functools import wraps
from enum import Enum


T = TypeVar('T')


class ValidationError(Exception):
    """Custom validation error with user-friendly messages"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


def validate_positive_amount(
    amount: Union[Decimal, float, int],
    field_name: str = "amount"
) -> Decimal:
    """
    Validate that an amount is positive.
    
    Args:
        amount: The amount to validate
        field_name: Name of the field for error messages
        
    Returns:
        Decimal representation of the amount
        
    Raises:
        ValidationError: If amount is not positive or invalid
    """
    if amount is None:
        raise ValidationError(
            f"{field_name} cannot be null",
            field=field_name
        )
    
    try:
        amount_decimal = Decimal(str(amount))
    except (ValueError, TypeError, Exception) as e:
        raise ValidationError(
            f"{field_name} must be a valid number, got {type(amount).__name__}",
            field=field_name
        )
    
    if amount_decimal.is_nan():
        raise ValidationError(
            f"{field_name} cannot be NaN",
            field=field_name
        )
    
    if amount_decimal.is_infinite():
        raise ValidationError(
            f"{field_name} cannot be infinite",
            field=field_name
        )
    
    if amount_decimal <= 0:
        raise ValidationError(
            f"{field_name} must be greater than 0, got {amount_decimal}",
            field=field_name
        )
    return amount_decimal


def validate_amount_range(
    amount: Union[Decimal, float, int],
    min_value: Optional[Union[Decimal, float, int]] = None,
    max_value: Optional[Union[Decimal, float, int]] = None,
    field_name: str = "amount"
) -> Decimal:
    """
    Validate that an amount is within a specified range.
    
    Args:
        amount: The amount to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Name of the field for error messages
        
    Returns:
        Decimal representation of the amount
        
    Raises:
        ValidationError: If amount is outside the range or invalid
    """
    if amount is None:
        raise ValidationError(
            f"{field_name} cannot be null",
            field=field_name
        )
    
    try:
        amount_decimal = Decimal(str(amount))
    except (ValueError, TypeError, Exception):
        raise ValidationError(
            f"{field_name} must be a valid number, got {type(amount).__name__}",
            field=field_name
        )
    
    if amount_decimal.is_nan():
        raise ValidationError(
            f"{field_name} cannot be NaN",
            field=field_name
        )
    
    if amount_decimal.is_infinite():
        raise ValidationError(
            f"{field_name} cannot be infinite",
            field=field_name
        )
    
    # Validate parameter consistency
    if min_value is not None and max_value is not None:
        min_decimal = Decimal(str(min_value))
        max_decimal = Decimal(str(max_value))
        if min_decimal > max_decimal:
            raise ValidationError(
                f"Invalid range: min_value ({min_decimal}) cannot be greater than max_value ({max_decimal})",
                field=field_name
            )
    
    if min_value is not None:
        min_decimal = Decimal(str(min_value))
        if amount_decimal < min_decimal:
            raise ValidationError(
                f"{field_name} must be at least {min_decimal}, got {amount_decimal}",
                field=field_name
            )
    
    if max_value is not None:
        max_decimal = Decimal(str(max_value))
        if amount_decimal > max_decimal:
            raise ValidationError(
                f"{field_name} must be at most {max_decimal}, got {amount_decimal}",
                field=field_name
            )
    
    return amount_decimal


def validate_non_empty_string(
    value: str,
    field_name: str = "value",
    min_length: int = 1,
    max_length: Optional[int] = None
) -> str:
    """
    Validate that a string is non-empty and optionally within length bounds.
    
    Args:
        value: The string to validate
        field_name: Name of the field for error messages
        min_length: Minimum required length (must be > 0)
        max_length: Maximum allowed length (must be >= min_length)
        
    Returns:
        Stripped string value
        
    Raises:
        ValidationError: If string is empty, outside length bounds, or parameters are invalid
    """
    # Validate parameters
    if min_length < 1:
        raise ValidationError(
            f"min_length must be at least 1, got {min_length}",
            field=field_name
        )
    
    if max_length is not None and max_length < min_length:
        raise ValidationError(
            f"max_length ({max_length}) cannot be less than min_length ({min_length})",
            field=field_name
        )
    
    if value is None:
        raise ValidationError(
            f"{field_name} cannot be null",
            field=field_name
        )
    
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be a string, got {type(value).__name__}",
            field=field_name
        )
    
    stripped = value.strip()
    
    if len(stripped) < min_length:
        raise ValidationError(
            f"{field_name} must be at least {min_length} characters, got {len(stripped)}",
            field=field_name
        )
    
    if max_length is not None and len(stripped) > max_length:
        raise ValidationError(
            f"{field_name} must be at most {max_length} characters, got {len(stripped)}",
            field=field_name
        )
    
    return stripped


def validate_enum_value(
    value: Any,
    enum_class: type[Enum],
    field_name: str = "value"
) -> Enum:
    """
    Validate that a value is a valid member of an enum.
    
    Args:
        value: The value to validate
        enum_class: The enum class to check against
        field_name: Name of the field for error messages
        
    Returns:
        The enum member
        
    Raises:
        ValidationError: If value is not a valid enum member
    """
    if value is None:
        raise ValidationError(
            f"{field_name} cannot be null",
            field=field_name
        )
    
    # If already an enum member, validate it's from the right enum
    if isinstance(value, Enum):
        if not isinstance(value, enum_class):
            raise ValidationError(
                f"{field_name} must be a {enum_class.__name__} value",
                field=field_name
            )
        return value
    
    # Try to convert string/value to enum
    try:
        if isinstance(value, str):
            return enum_class[value]
        else:
            return enum_class(value)
    except (KeyError, ValueError):
        valid_values = [e.name for e in enum_class]
        raise ValidationError(
            f"{field_name} must be one of {valid_values}, got {value}",
            field=field_name
        )


def validate_date_range(
    date: datetime,
    min_date: Optional[datetime] = None,
    max_date: Optional[datetime] = None,
    field_name: str = "date"
) -> datetime:
    """
    Validate that a date is within a specified range.
    
    Args:
        date: The date to validate
        min_date: Minimum allowed date (inclusive)
        max_date: Maximum allowed date (inclusive)
        field_name: Name of the field for error messages
        
    Returns:
        The validated datetime
        
    Raises:
        ValidationError: If date is outside the range or invalid
    """
    if date is None:
        raise ValidationError(
            f"{field_name} cannot be null",
            field=field_name
        )
    
    # Validate parameter consistency
    if min_date is not None and max_date is not None:
        if min_date > max_date:
            raise ValidationError(
                f"Invalid date range: min_date ({min_date.isoformat()}) cannot be after max_date ({max_date.isoformat()})",
                field=field_name
            )
    
    if min_date is not None and date < min_date:
        raise ValidationError(
            f"{field_name} must be on or after {min_date.isoformat()}, got {date.isoformat()}",
            field=field_name
        )
    
    if max_date is not None and date > max_date:
        raise ValidationError(
            f"{field_name} must be on or before {max_date.isoformat()}, got {date.isoformat()}",
            field=field_name
        )
    
    return date


def validate_in_list(
    value: Any,
    allowed_values: List[Any],
    field_name: str = "value"
) -> Any:
    """
    Validate that a value is in a list of allowed values.
    
    Args:
        value: The value to validate
        allowed_values: List of allowed values (must not be empty)
        field_name: Name of the field for error messages
        
    Returns:
        The validated value
        
    Raises:
        ValidationError: If value is not in the allowed list or list is invalid
    """
    if allowed_values is None:
        raise ValidationError(
            f"allowed_values cannot be null for {field_name}",
            field=field_name
        )
    
    if not allowed_values:
        raise ValidationError(
            f"allowed_values cannot be empty for {field_name}",
            field=field_name
        )
    
    if value not in allowed_values:
        raise ValidationError(
            f"{field_name} must be one of {allowed_values}, got {value}",
            field=field_name
        )
    return value


def validate_not_null(
    value: Any,
    field_name: str = "value"
) -> Any:
    """
    Validate that a value is not None.
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        The validated value
        
    Raises:
        ValidationError: If value is None
    """
    if value is None:
        raise ValidationError(
            f"{field_name} is required and cannot be null",
            field=field_name
        )
    return value


def validate_all(*validators: Callable[[], Any]) -> None:
    """
    Execute multiple validation functions and collect all errors.
    
    Args:
        *validators: Validation functions to execute
        
    Raises:
        ValidationError: If any validation fails, with combined error messages
    """
    errors = []
    
    for validator in validators:
        try:
            validator()
        except ValidationError as e:
            errors.append(e)
    
    if errors:
        # Combine all error messages
        combined_message = "; ".join(e.message for e in errors)
        raise ValidationError(combined_message)


def create_validation_response(
    is_valid: bool,
    errors: Optional[List[str]] = None,
    data: Optional[Any] = None
) -> dict:
    """
    Create a standardized validation response.
    
    Args:
        is_valid: Whether validation passed
        errors: List of error messages (if validation failed)
        data: Optional validated data
        
    Returns:
        Dictionary with validation result
    """
    response = {
        "is_valid": is_valid,
        "errors": errors or []
    }
    if data is not None:
        response["data"] = data
    return response
