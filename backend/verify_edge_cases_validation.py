#!/usr/bin/env python3
"""
Verification script for validation utility edge cases
Tests all the tightened edge-case handling
"""
import sys
from decimal import Decimal
from datetime import datetime, timedelta
from app.utils.validation import (
    ValidationError,
    validate_positive_amount,
    validate_amount_range,
    validate_non_empty_string,
    validate_enum_value,
    validate_date_range,
    validate_in_list,
)
from app.models.transaction import TransactionStatus

def test_positive_amount_edge_cases():
    """Test edge cases in validate_positive_amount"""
    print("Testing validate_positive_amount edge cases...")
    
    # Test None
    try:
        validate_positive_amount(None)
        print("  ✗ None should raise error")
        return False
    except ValidationError as e:
        if "cannot be null" in e.message:
            print("  ✓ None rejected correctly")
        else:
            print(f"  ✗ Wrong error for None: {e.message}")
            return False
    
    # Test NaN
    try:
        validate_positive_amount(float('nan'))
        print("  ✗ NaN should raise error")
        return False
    except ValidationError as e:
        if "cannot be NaN" in e.message:
            print("  ✓ NaN rejected correctly")
        else:
            print(f"  ✗ Wrong error for NaN: {e.message}")
            return False
    
    # Test Infinity
    try:
        validate_positive_amount(float('inf'))
        print("  ✗ Infinity should raise error")
        return False
    except ValidationError as e:
        if "cannot be infinite" in e.message:
            print("  ✓ Infinity rejected correctly")
        else:
            print(f"  ✗ Wrong error for Infinity: {e.message}")
            return False
    
    # Test invalid type
    try:
        validate_positive_amount([100])
        print("  ✗ List should raise error")
        return False
    except ValidationError as e:
        if "must be a valid number" in e.message:
            print("  ✓ Invalid type rejected correctly")
        else:
            print(f"  ✗ Wrong error for list: {e.message}")
            return False
    
    # Test valid values still work
    try:
        result = validate_positive_amount(100.50)
        if result == Decimal("100.50"):
            print("  ✓ Valid positive amount still works")
        else:
            print(f"  ✗ Valid amount returned wrong value: {result}")
            return False
    except Exception as e:
        print(f"  ✗ Valid amount raised error: {e}")
        return False
    
    return True

def test_amount_range_edge_cases():
    """Test edge cases in validate_amount_range"""
    print("\nTesting validate_amount_range edge cases...")
    
    # Test None
    try:
        validate_amount_range(None, min_value=10, max_value=100)
        print("  ✗ None should raise error")
        return False
    except ValidationError as e:
        if "cannot be null" in e.message:
            print("  ✓ None rejected correctly")
        else:
            print(f"  ✗ Wrong error for None: {e.message}")
            return False
    
    # Test NaN
    try:
        validate_amount_range(float('nan'), min_value=10, max_value=100)
        print("  ✗ NaN should raise error")
        return False
    except ValidationError as e:
        if "cannot be NaN" in e.message:
            print("  ✓ NaN rejected correctly")
        else:
            print(f"  ✗ Wrong error for NaN: {e.message}")
            return False
    
    # Test min > max
    try:
        validate_amount_range(50, min_value=100, max_value=10)
        print("  ✗ min > max should raise error")
        return False
    except ValidationError as e:
        if "Invalid range" in e.message and "cannot be greater than" in e.message:
            print("  ✓ min > max rejected correctly")
        else:
            print(f"  ✗ Wrong error for min > max: {e.message}")
            return False
    
    # Test valid range still works
    try:
        result = validate_amount_range(50, min_value=10, max_value=100)
        if result == Decimal("50"):
            print("  ✓ Valid range still works")
        else:
            print(f"  ✗ Valid range returned wrong value: {result}")
            return False
    except Exception as e:
        print(f"  ✗ Valid range raised error: {e}")
        return False
    
    return True

def test_non_empty_string_edge_cases():
    """Test edge cases in validate_non_empty_string"""
    print("\nTesting validate_non_empty_string edge cases...")
    
    # Test None
    try:
        validate_non_empty_string(None)
        print("  ✗ None should raise error")
        return False
    except ValidationError as e:
        if "cannot be null" in e.message:
            print("  ✓ None rejected correctly")
        else:
            print(f"  ✗ Wrong error for None: {e.message}")
            return False
    
    # Test negative min_length
    try:
        validate_non_empty_string("test", min_length=-1)
        print("  ✗ Negative min_length should raise error")
        return False
    except ValidationError as e:
        if "min_length must be at least 1" in e.message:
            print("  ✓ Negative min_length rejected correctly")
        else:
            print(f"  ✗ Wrong error for negative min_length: {e.message}")
            return False
    
    # Test zero min_length
    try:
        validate_non_empty_string("test", min_length=0)
        print("  ✗ Zero min_length should raise error")
        return False
    except ValidationError as e:
        if "min_length must be at least 1" in e.message:
            print("  ✓ Zero min_length rejected correctly")
        else:
            print(f"  ✗ Wrong error for zero min_length: {e.message}")
            return False
    
    # Test max < min
    try:
        validate_non_empty_string("test", min_length=10, max_length=5)
        print("  ✗ max < min should raise error")
        return False
    except ValidationError as e:
        if "cannot be less than min_length" in e.message:
            print("  ✓ max < min rejected correctly")
        else:
            print(f"  ✗ Wrong error for max < min: {e.message}")
            return False
    
    # Test valid string still works
    try:
        result = validate_non_empty_string("  Hello  ")
        if result == "Hello":
            print("  ✓ Valid string still works")
        else:
            print(f"  ✗ Valid string returned wrong value: {result}")
            return False
    except Exception as e:
        print(f"  ✗ Valid string raised error: {e}")
        return False
    
    return True

def test_enum_value_edge_cases():
    """Test edge cases in validate_enum_value"""
    print("\nTesting validate_enum_value edge cases...")
    
    # Test None
    try:
        validate_enum_value(None, TransactionStatus)
        print("  ✗ None should raise error")
        return False
    except ValidationError as e:
        if "cannot be null" in e.message:
            print("  ✓ None rejected correctly")
        else:
            print(f"  ✗ Wrong error for None: {e.message}")
            return False
    
    # Test valid enum still works
    try:
        result = validate_enum_value("APPROVED", TransactionStatus)
        if result == TransactionStatus.APPROVED:
            print("  ✓ Valid enum still works")
        else:
            print(f"  ✗ Valid enum returned wrong value: {result}")
            return False
    except Exception as e:
        print(f"  ✗ Valid enum raised error: {e}")
        return False
    
    return True

def test_date_range_edge_cases():
    """Test edge cases in validate_date_range"""
    print("\nTesting validate_date_range edge cases...")
    
    # Test None
    try:
        validate_date_range(None)
        print("  ✗ None should raise error")
        return False
    except ValidationError as e:
        if "cannot be null" in e.message:
            print("  ✓ None rejected correctly")
        else:
            print(f"  ✗ Wrong error for None: {e.message}")
            return False
    
    # Test min > max
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)
    
    try:
        validate_date_range(now, min_date=tomorrow, max_date=yesterday)
        print("  ✗ min_date > max_date should raise error")
        return False
    except ValidationError as e:
        if "Invalid date range" in e.message and "cannot be after" in e.message:
            print("  ✓ min_date > max_date rejected correctly")
        else:
            print(f"  ✗ Wrong error for min > max: {e.message}")
            return False
    
    # Test valid date still works
    try:
        result = validate_date_range(now, min_date=yesterday, max_date=tomorrow)
        if result == now:
            print("  ✓ Valid date range still works")
        else:
            print(f"  ✗ Valid date returned wrong value: {result}")
            return False
    except Exception as e:
        print(f"  ✗ Valid date raised error: {e}")
        return False
    
    return True

def test_in_list_edge_cases():
    """Test edge cases in validate_in_list"""
    print("\nTesting validate_in_list edge cases...")
    
    # Test None allowed_values
    try:
        validate_in_list("test", None)
        print("  ✗ None allowed_values should raise error")
        return False
    except ValidationError as e:
        if "allowed_values cannot be null" in e.message:
            print("  ✓ None allowed_values rejected correctly")
        else:
            print(f"  ✗ Wrong error for None allowed_values: {e.message}")
            return False
    
    # Test empty allowed_values
    try:
        validate_in_list("test", [])
        print("  ✗ Empty allowed_values should raise error")
        return False
    except ValidationError as e:
        if "allowed_values cannot be empty" in e.message:
            print("  ✓ Empty allowed_values rejected correctly")
        else:
            print(f"  ✗ Wrong error for empty allowed_values: {e.message}")
            return False
    
    # Test valid list still works
    try:
        result = validate_in_list("red", ["red", "green", "blue"])
        if result == "red":
            print("  ✓ Valid list still works")
        else:
            print(f"  ✗ Valid list returned wrong value: {result}")
            return False
    except Exception as e:
        print(f"  ✗ Valid list raised error: {e}")
        return False
    
    return True

def main():
    """Run all edge case tests"""
    print("=" * 60)
    print("Validation Edge Case Verification")
    print("=" * 60)
    
    all_passed = True
    
    all_passed = test_positive_amount_edge_cases() and all_passed
    all_passed = test_amount_range_edge_cases() and all_passed
    all_passed = test_non_empty_string_edge_cases() and all_passed
    all_passed = test_enum_value_edge_cases() and all_passed
    all_passed = test_date_range_edge_cases() and all_passed
    all_passed = test_in_list_edge_cases() and all_passed
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All edge case tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some edge case tests failed")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
