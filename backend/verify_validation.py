#!/usr/bin/env python3
"""
Verification script for validation utilities.
Demonstrates key validation functions work as expected.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from app.utils.validation import (
    ValidationError,
    validate_positive_amount,
    validate_amount_range,
    validate_non_empty_string,
    validate_in_list,
    validate_not_null,
    validate_date_range,
    create_validation_response
)


def test_positive_amount():
    """Test positive amount validation"""
    print("Testing positive amount validation...")
    
    # Valid cases
    assert validate_positive_amount(100) == Decimal("100")
    assert validate_positive_amount(99.99) == Decimal("99.99")
    print("  ✓ Valid positive amounts pass")
    
    # Invalid cases
    try:
        validate_positive_amount(0)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be greater than 0" in e.message
        print("  ✓ Zero amount rejected")
    
    try:
        validate_positive_amount(-50)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be greater than 0" in e.message
        print("  ✓ Negative amount rejected")


def test_amount_range():
    """Test amount range validation"""
    print("\nTesting amount range validation...")
    
    # Valid cases
    assert validate_amount_range(50, min_value=10, max_value=100) == Decimal("50")
    assert validate_amount_range(10, min_value=10) == Decimal("10")
    assert validate_amount_range(100, max_value=100) == Decimal("100")
    print("  ✓ Valid amounts within range pass")
    
    # Invalid cases
    try:
        validate_amount_range(5, min_value=10)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be at least" in e.message
        print("  ✓ Amount below minimum rejected")
    
    try:
        validate_amount_range(150, max_value=100)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be at most" in e.message
        print("  ✓ Amount above maximum rejected")


def test_non_empty_string():
    """Test non-empty string validation"""
    print("\nTesting non-empty string validation...")
    
    # Valid cases
    assert validate_non_empty_string("Hello") == "Hello"
    assert validate_non_empty_string("  Test  ") == "Test"
    print("  ✓ Valid strings pass (whitespace trimmed)")
    
    # Invalid cases
    try:
        validate_non_empty_string("")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be at least" in e.message
        print("  ✓ Empty string rejected")
    
    try:
        validate_non_empty_string("Hi", min_length=5)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be at least 5 characters" in e.message
        print("  ✓ String below minimum length rejected")
    
    try:
        validate_non_empty_string("Hello World", max_length=5)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be at most 5 characters" in e.message
        print("  ✓ String above maximum length rejected")


def test_in_list():
    """Test in-list validation"""
    print("\nTesting in-list validation...")
    
    # Valid cases
    allowed = ["APPROVED", "REJECTED", "ESCALATED"]
    assert validate_in_list("APPROVED", allowed) == "APPROVED"
    print("  ✓ Valid values in list pass")
    
    # Invalid cases
    try:
        validate_in_list("CLEARED", allowed)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be one of" in e.message
        print("  ✓ Value not in list rejected")


def test_not_null():
    """Test not-null validation"""
    print("\nTesting not-null validation...")
    
    # Valid cases
    assert validate_not_null("Hello") == "Hello"
    assert validate_not_null(0) == 0
    assert validate_not_null("") == ""
    print("  ✓ Non-null values pass")
    
    # Invalid cases
    try:
        validate_not_null(None)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "cannot be null" in e.message
        print("  ✓ None value rejected")


def test_date_range():
    """Test date range validation"""
    print("\nTesting date range validation...")
    
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)
    
    # Valid cases
    assert validate_date_range(now, min_date=yesterday, max_date=tomorrow) == now
    print("  ✓ Valid dates within range pass")
    
    # Invalid cases
    try:
        validate_date_range(yesterday, min_date=now)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be on or after" in e.message
        print("  ✓ Date before minimum rejected")
    
    try:
        validate_date_range(tomorrow, max_date=now)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "must be on or before" in e.message
        print("  ✓ Date after maximum rejected")


def test_validation_response():
    """Test validation response creation"""
    print("\nTesting validation response creation...")
    
    # Valid response
    response = create_validation_response(is_valid=True)
    assert response["is_valid"] is True
    assert response["errors"] == []
    print("  ✓ Valid response structure created")
    
    # Invalid response with errors
    errors = ["Error 1", "Error 2"]
    response = create_validation_response(is_valid=False, errors=errors)
    assert response["is_valid"] is False
    assert response["errors"] == errors
    print("  ✓ Invalid response with errors created")
    
    # Response with data
    data = {"id": 1, "name": "Test"}
    response = create_validation_response(is_valid=True, data=data)
    assert response["data"] == data
    print("  ✓ Response with data created")


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("Validation Utility Verification")
    print("=" * 60)
    
    try:
        test_positive_amount()
        test_amount_range()
        test_non_empty_string()
        test_in_list()
        test_not_null()
        test_date_range()
        test_validation_response()
        
        print("\n" + "=" * 60)
        print("✓ All verification tests passed!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
