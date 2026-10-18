"""Tests for validation utilities"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum
from app.utils.validation import (
    ValidationError,
    validate_positive_amount,
    validate_amount_range,
    validate_non_empty_string,
    validate_enum_value,
    validate_date_range,
    validate_in_list,
    validate_not_null,
    validate_all,
    create_validation_response
)
from app.models.transaction import TransactionStatus


class TestStatus(Enum):
    """Test enum for validation"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class TestValidatePositiveAmount:
    """Tests for validate_positive_amount function"""
    
    def test_valid_positive_decimal(self):
        """Test validation with valid positive decimal"""
        result = validate_positive_amount(Decimal("100.50"))
        assert result == Decimal("100.50")
    
    def test_valid_positive_int(self):
        """Test validation with valid positive integer"""
        result = validate_positive_amount(100)
        assert result == Decimal("100")
    
    def test_valid_positive_float(self):
        """Test validation with valid positive float"""
        result = validate_positive_amount(99.99)
        assert result == Decimal("99.99")
    
    def test_zero_raises_error(self):
        """Test that zero raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_amount(0)
        assert "must be greater than 0" in exc_info.value.message
        assert exc_info.value.field == "amount"
    
    def test_negative_raises_error(self):
        """Test that negative value raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_amount(-50.00)
        assert "must be greater than 0" in exc_info.value.message
    
    def test_custom_field_name(self):
        """Test custom field name in error message"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_amount(-10, field_name="price")
        assert "price must be greater than 0" in exc_info.value.message
        assert exc_info.value.field == "price"
    
    def test_none_raises_error(self):
        """Test that None raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_amount(None)
        assert "cannot be null" in exc_info.value.message
    
    def test_nan_raises_error(self):
        """Test that NaN raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_amount(float('nan'))
        assert "cannot be NaN" in exc_info.value.message
    
    def test_infinity_raises_error(self):
        """Test that infinity raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_amount(float('inf'))
        assert "cannot be infinite" in exc_info.value.message
    
    def test_invalid_type_raises_error(self):
        """Test that invalid type raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_amount([100])
        assert "must be a valid number" in exc_info.value.message


class TestValidateAmountRange:
    """Tests for validate_amount_range function"""
    
    def test_amount_within_range(self):
        """Test amount within valid range"""
        result = validate_amount_range(50, min_value=10, max_value=100)
        assert result == Decimal("50")
    
    def test_amount_at_min_boundary(self):
        """Test amount at minimum boundary"""
        result = validate_amount_range(10, min_value=10, max_value=100)
        assert result == Decimal("10")
    
    def test_amount_at_max_boundary(self):
        """Test amount at maximum boundary"""
        result = validate_amount_range(100, min_value=10, max_value=100)
        assert result == Decimal("100")
    
    def test_amount_below_min_raises_error(self):
        """Test amount below minimum raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_amount_range(5, min_value=10)
        assert "must be at least 10" in exc_info.value.message
    
    def test_amount_above_max_raises_error(self):
        """Test amount above maximum raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_amount_range(150, max_value=100)
        assert "must be at most 100" in exc_info.value.message
    
    def test_only_min_value(self):
        """Test validation with only minimum value"""
        result = validate_amount_range(50, min_value=10)
        assert result == Decimal("50")
    
    def test_only_max_value(self):
        """Test validation with only maximum value"""
        result = validate_amount_range(50, max_value=100)
        assert result == Decimal("50")
    
    def test_no_limits(self):
        """Test validation with no limits"""
        result = validate_amount_range(12345.67)
        assert result == Decimal("12345.67")
    
    def test_custom_field_name(self):
        """Test custom field name in error message"""
        with pytest.raises(ValidationError) as exc_info:
            validate_amount_range(5, min_value=10, field_name="balance")
        assert "balance must be at least" in exc_info.value.message
    
    def test_none_raises_error(self):
        """Test that None raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_amount_range(None, min_value=10, max_value=100)
        assert "cannot be null" in exc_info.value.message
    
    def test_nan_raises_error(self):
        """Test that NaN raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_amount_range(float('nan'), min_value=10, max_value=100)
        assert "cannot be NaN" in exc_info.value.message
    
    def test_infinity_raises_error(self):
        """Test that infinity raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_amount_range(float('inf'), min_value=10, max_value=100)
        assert "cannot be infinite" in exc_info.value.message
    
    def test_min_greater_than_max_raises_error(self):
        """Test that min > max raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_amount_range(50, min_value=100, max_value=10)
        assert "Invalid range" in exc_info.value.message
        assert "cannot be greater than" in exc_info.value.message
    
    def test_invalid_type_raises_error(self):
        """Test that invalid type raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_amount_range("invalid", min_value=10, max_value=100)
        assert "must be a valid number" in exc_info.value.message


class TestValidateNonEmptyString:
    """Tests for validate_non_empty_string function"""
    
    def test_valid_string(self):
        """Test validation with valid string"""
        result = validate_non_empty_string("Hello World")
        assert result == "Hello World"
    
    def test_string_with_whitespace_stripped(self):
        """Test that whitespace is stripped"""
        result = validate_non_empty_string("  Hello  ")
        assert result == "Hello"
    
    def test_empty_string_raises_error(self):
        """Test that empty string raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string("")
        assert "must be at least 1 characters" in exc_info.value.message
    
    def test_whitespace_only_raises_error(self):
        """Test that whitespace-only string raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string("   ")
        assert "must be at least 1 characters" in exc_info.value.message
    
    def test_min_length_validation(self):
        """Test minimum length validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string("Hi", min_length=5)
        assert "must be at least 5 characters" in exc_info.value.message
    
    def test_max_length_validation(self):
        """Test maximum length validation"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string("Hello World", max_length=5)
        assert "must be at most 5 characters" in exc_info.value.message
    
    def test_min_max_length_validation(self):
        """Test both min and max length validation"""
        result = validate_non_empty_string("Hello", min_length=3, max_length=10)
        assert result == "Hello"
    
    def test_non_string_raises_error(self):
        """Test that non-string type raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string(123)
        assert "must be a string" in exc_info.value.message
    
    def test_custom_field_name(self):
        """Test custom field name in error message"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string("", field_name="username")
        assert "username must be at least" in exc_info.value.message
        assert exc_info.value.field == "username"
    
    def test_none_raises_error(self):
        """Test that None raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string(None)
        assert "cannot be null" in exc_info.value.message
    
    def test_negative_min_length_raises_error(self):
        """Test that negative min_length raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string("test", min_length=-1)
        assert "min_length must be at least 1" in exc_info.value.message
    
    def test_zero_min_length_raises_error(self):
        """Test that zero min_length raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string("test", min_length=0)
        assert "min_length must be at least 1" in exc_info.value.message
    
    def test_max_less_than_min_raises_error(self):
        """Test that max_length < min_length raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_non_empty_string("test", min_length=10, max_length=5)
        assert "cannot be less than min_length" in exc_info.value.message


class TestValidateEnumValue:
    """Tests for validate_enum_value function"""
    
    def test_valid_enum_member(self):
        """Test validation with valid enum member"""
        result = validate_enum_value(TestStatus.ACTIVE, TestStatus)
        assert result == TestStatus.ACTIVE
    
    def test_valid_string_to_enum(self):
        """Test conversion from valid string to enum"""
        result = validate_enum_value("ACTIVE", TestStatus)
        assert result == TestStatus.ACTIVE
    
    def test_transaction_status_enum(self):
        """Test with real TransactionStatus enum"""
        result = validate_enum_value("APPROVED", TransactionStatus)
        assert result == TransactionStatus.APPROVED
    
    def test_invalid_string_raises_error(self):
        """Test that invalid string raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_enum_value("INVALID", TestStatus)
        assert "must be one of" in exc_info.value.message
        assert "ACTIVE" in exc_info.value.message
    
    def test_wrong_enum_type_raises_error(self):
        """Test that wrong enum type raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_enum_value(TransactionStatus.APPROVED, TestStatus)
        assert "must be a TestStatus value" in exc_info.value.message
    
    def test_custom_field_name(self):
        """Test custom field name in error message"""
        with pytest.raises(ValidationError) as exc_info:
            validate_enum_value("INVALID", TestStatus, field_name="status")
        assert "status must be one of" in exc_info.value.message
    
    def test_none_raises_error(self):
        """Test that None raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_enum_value(None, TestStatus)
        assert "cannot be null" in exc_info.value.message


class TestValidateDateRange:
    """Tests for validate_date_range function"""
    
    def test_date_within_range(self):
        """Test date within valid range"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        result = validate_date_range(now, min_date=yesterday, max_date=tomorrow)
        assert result == now
    
    def test_date_at_min_boundary(self):
        """Test date at minimum boundary"""
        now = datetime.now()
        result = validate_date_range(now, min_date=now)
        assert result == now
    
    def test_date_at_max_boundary(self):
        """Test date at maximum boundary"""
        now = datetime.now()
        result = validate_date_range(now, max_date=now)
        assert result == now
    
    def test_date_before_min_raises_error(self):
        """Test date before minimum raises error"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(yesterday, min_date=now)
        assert "must be on or after" in exc_info.value.message
    
    def test_date_after_max_raises_error(self):
        """Test date after maximum raises error"""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(tomorrow, max_date=now)
        assert "must be on or before" in exc_info.value.message
    
    def test_only_min_date(self):
        """Test validation with only minimum date"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        result = validate_date_range(now, min_date=yesterday)
        assert result == now
    
    def test_only_max_date(self):
        """Test validation with only maximum date"""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        result = validate_date_range(now, max_date=tomorrow)
        assert result == now
    
    def test_no_limits(self):
        """Test validation with no limits"""
        now = datetime.now()
        result = validate_date_range(now)
        assert result == now
    
    def test_custom_field_name(self):
        """Test custom field name in error message"""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(tomorrow, max_date=now, field_name="transaction_date")
        assert "transaction_date must be on or before" in exc_info.value.message
    
    def test_none_raises_error(self):
        """Test that None raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(None)
        assert "cannot be null" in exc_info.value.message
    
    def test_min_after_max_raises_error(self):
        """Test that min_date > max_date raises ValidationError"""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        with pytest.raises(ValidationError) as exc_info:
            validate_date_range(now, min_date=tomorrow, max_date=yesterday)
        assert "Invalid date range" in exc_info.value.message
        assert "cannot be after" in exc_info.value.message


class TestValidateInList:
    """Tests for validate_in_list function"""
    
    def test_value_in_list(self):
        """Test value that is in the list"""
        allowed = ["red", "green", "blue"]
        result = validate_in_list("red", allowed)
        assert result == "red"
    
    def test_value_not_in_list_raises_error(self):
        """Test value not in list raises error"""
        allowed = ["red", "green", "blue"]
        with pytest.raises(ValidationError) as exc_info:
            validate_in_list("yellow", allowed)
        assert "must be one of" in exc_info.value.message
    
    def test_with_integers(self):
        """Test validation with integer values"""
        allowed = [1, 2, 3, 4, 5]
        result = validate_in_list(3, allowed)
        assert result == 3
    
    def test_with_enums(self):
        """Test validation with enum values"""
        allowed = [TestStatus.ACTIVE, TestStatus.PENDING]
        result = validate_in_list(TestStatus.ACTIVE, allowed)
        assert result == TestStatus.ACTIVE
    
    def test_custom_field_name(self):
        """Test custom field name in error message"""
        allowed = ["option1", "option2"]
        with pytest.raises(ValidationError) as exc_info:
            validate_in_list("option3", allowed, field_name="choice")
        assert "choice must be one of" in exc_info.value.message
        assert exc_info.value.field == "choice"
    
    def test_none_allowed_values_raises_error(self):
        """Test that None allowed_values raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_in_list("test", None)
        assert "allowed_values cannot be null" in exc_info.value.message
    
    def test_empty_allowed_values_raises_error(self):
        """Test that empty allowed_values raises ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_in_list("test", [])
        assert "allowed_values cannot be empty" in exc_info.value.message


class TestValidateNotNull:
    """Tests for validate_not_null function"""
    
    def test_non_null_value(self):
        """Test validation with non-null value"""
        result = validate_not_null("Hello")
        assert result == "Hello"
    
    def test_zero_is_valid(self):
        """Test that zero is considered valid (not null)"""
        result = validate_not_null(0)
        assert result == 0
    
    def test_empty_string_is_valid(self):
        """Test that empty string is considered valid (not null)"""
        result = validate_not_null("")
        assert result == ""
    
    def test_false_is_valid(self):
        """Test that False is considered valid (not null)"""
        result = validate_not_null(False)
        assert result is False
    
    def test_none_raises_error(self):
        """Test that None raises error"""
        with pytest.raises(ValidationError) as exc_info:
            validate_not_null(None)
        assert "is required and cannot be null" in exc_info.value.message
    
    def test_custom_field_name(self):
        """Test custom field name in error message"""
        with pytest.raises(ValidationError) as exc_info:
            validate_not_null(None, field_name="user_id")
        assert "user_id is required and cannot be null" in exc_info.value.message


class TestValidateAll:
    """Tests for validate_all function"""
    
    def test_all_validators_pass(self):
        """Test when all validators pass"""
        value1 = "test"
        value2 = 100
        
        validate_all(
            lambda: validate_non_empty_string(value1),
            lambda: validate_positive_amount(value2)
        )
        # Should not raise any exception
    
    def test_single_validator_fails(self):
        """Test when one validator fails"""
        with pytest.raises(ValidationError) as exc_info:
            validate_all(
                lambda: validate_positive_amount(-10),
                lambda: validate_non_empty_string("valid")
            )
        assert "must be greater than 0" in exc_info.value.message
    
    def test_multiple_validators_fail(self):
        """Test when multiple validators fail"""
        with pytest.raises(ValidationError) as exc_info:
            validate_all(
                lambda: validate_positive_amount(-10),
                lambda: validate_non_empty_string("")
            )
        # Should contain both error messages
        assert "must be greater than 0" in exc_info.value.message
        assert "must be at least 1 characters" in exc_info.value.message
    
    def test_no_validators(self):
        """Test with no validators"""
        validate_all()  # Should not raise any exception


class TestCreateValidationResponse:
    """Tests for create_validation_response function"""
    
    def test_valid_response(self):
        """Test creating a valid response"""
        response = create_validation_response(is_valid=True)
        assert response["is_valid"] is True
        assert response["errors"] == []
    
    def test_invalid_response_with_errors(self):
        """Test creating an invalid response with errors"""
        errors = ["Error 1", "Error 2"]
        response = create_validation_response(is_valid=False, errors=errors)
        assert response["is_valid"] is False
        assert response["errors"] == errors
    
    def test_response_with_data(self):
        """Test creating a response with data"""
        data = {"id": 1, "name": "Test"}
        response = create_validation_response(is_valid=True, data=data)
        assert response["is_valid"] is True
        assert response["data"] == data
    
    def test_response_without_data(self):
        """Test creating a response without data"""
        response = create_validation_response(is_valid=True)
        assert "data" not in response


class TestValidationIntegration:
    """Integration tests with actual API endpoints"""
    
    def test_review_transaction_with_valid_data(self, client, sample_transaction):
        """Test review endpoint with valid data using validation helper"""
        # Update transaction to HELD status first
        sample_transaction.status = TransactionStatus.HELD
        
        review_data = {
            "decision": "APPROVED",
            "notes": "Transaction looks legitimate",
            "reviewed_by": "analyst@bank.com"
        }
        
        response = client.post(
            f"/api/v1/transactions/{sample_transaction.id}/review",
            json=review_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["reviewed_by"] == "analyst@bank.com"
    
    def test_review_transaction_with_empty_notes(self, client, sample_transaction):
        """Test review endpoint with empty notes (should fail validation)"""
        review_data = {
            "decision": "APPROVED",
            "notes": "",
            "reviewed_by": "analyst@bank.com"
        }
        
        response = client.post(
            f"/api/v1/transactions/{sample_transaction.id}/review",
            json=review_data
        )
        
        # Pydantic validation will catch this first
        assert response.status_code == 422
    
    def test_review_transaction_with_invalid_decision(self, client, sample_transaction):
        """Test review endpoint with invalid decision"""
        review_data = {
            "decision": "CLEARED",  # Not a valid review decision
            "notes": "Some notes",
            "reviewed_by": "analyst@bank.com"
        }
        
        response = client.post(
            f"/api/v1/transactions/{sample_transaction.id}/review",
            json=review_data
        )
        
        assert response.status_code == 400
        assert "must be one of" in response.json()["detail"]
    
    def test_review_transaction_with_whitespace_notes(self, client, sample_transaction):
        """Test review endpoint with whitespace-only notes"""
        review_data = {
            "decision": "APPROVED",
            "notes": "   ",
            "reviewed_by": "analyst@bank.com"
        }
        
        response = client.post(
            f"/api/v1/transactions/{sample_transaction.id}/review",
            json=review_data
        )
        
        # Pydantic validation will catch this
        assert response.status_code == 422


class TestValidationErrorClass:
    """Tests for ValidationError class"""
    
    def test_error_with_message_only(self):
        """Test ValidationError with message only"""
        error = ValidationError("Test error")
        assert error.message == "Test error"
        assert error.field is None
        assert str(error) == "Test error"
    
    def test_error_with_field(self):
        """Test ValidationError with field name"""
        error = ValidationError("Test error", field="test_field")
        assert error.message == "Test error"
        assert error.field == "test_field"
