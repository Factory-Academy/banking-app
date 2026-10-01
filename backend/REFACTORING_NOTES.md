# Fraud Detection Config Refactoring

## Overview
Introduced a centralized dataclass configuration to replace scattered module constants across the fraud detection service. This improves maintainability, testability, and makes it easier to customize fraud detection behavior.

## Changes Made

### 1. New Files Created

#### `app/config/__init__.py` (4 lines)
- Package initialization for config module
- Exports `FraudDetectionConfig` and `get_fraud_config()`

#### `app/config/fraud_detection_config.py` (124 lines)
- **FraudDetectionConfig**: Frozen dataclass containing all fraud detection constants
- Centralized 18 previously scattered constants:
  - Rule thresholds (amount, velocity, geographic, time, deviation)
  - Risk level thresholds (HIGH: 70, MEDIUM: 40)
  - Risk points per rule (30, 40, 50, 20, 25, 35)
- **Validation**: Comprehensive `__post_init__` validation
  - Ensures positive values for thresholds
  - Validates hour ranges (0-23, 0-24)
  - Ensures high_risk > medium_risk
  - Non-negative risk points
- **Immutability**: Uses `frozen=True` to prevent runtime modifications
- **get_fraud_config()**: Returns singleton default config instance

#### `tests/test_fraud_detection_config.py` (321 lines)
- 50+ comprehensive unit tests organized in 6 test classes:
  - `TestFraudDetectionConfigDefaults`: Verify all 18 default values
  - `TestFraudDetectionConfigImmutability`: Ensure frozen behavior
  - `TestFraudDetectionConfigValidation`: Test all 20+ validation rules
  - `TestFraudDetectionConfigCustomValues`: Test custom configurations
  - `TestGetFraudConfig`: Test singleton behavior
  - `TestFraudDetectionConfigEdgeCases`: Test boundary conditions

### 2. Files Modified

#### `app/services/fraud_detection.py` (195 lines)
Updated all fraud detection classes to use config:

**HighAmountRule**:
- Added `config` parameter (optional, defaults to `get_fraud_config()`)
- Now uses `config.high_amount_threshold` instead of hardcoded `Decimal("10000")`
- Uses `config.high_amount_points` for risk points

**VelocityRule**:
- Now uses `config.velocity_max_transactions` (was: 5)
- Now uses `config.velocity_time_window_hours` (was: 1)
- Uses `config.velocity_points` for risk points

**GeographicAnomalyRule**:
- Now uses `config.geographic_time_window_hours` (was: 4)
- Now uses `config.geographic_distance_threshold_km` (was: 500)
- Uses `config.geographic_anomaly_points` for risk points

**UnusualTimeRule**:
- Now uses `config.unusual_time_start_hour` (was: 2)
- Now uses `config.unusual_time_end_hour` (was: 5)
- Uses `config.unusual_time_points` for risk points

**FirstInternationalRule**:
- Now uses `config.home_country_code` (was: "US")
- Uses `config.first_international_points` for risk points

**AmountDeviationRule**:
- Now uses `config.amount_deviation_multiplier` (was: 3)
- Now uses `config.amount_deviation_min_transactions` (was: 3)
- Uses `config.amount_deviation_points` for risk points

**FraudDetectionService**:
- Added `config` parameter (optional)
- Passes config to all rule instances
- Uses `config.high_risk_threshold` (was: 70)
- Uses `config.medium_risk_threshold` (was: 40)

## Backward Compatibility

✅ **Fully backward compatible** - existing code continues to work:

```python
# Old usage still works (uses default config)
service = FraudDetectionService()
rule = HighAmountRule()

# New usage allows customization
custom_config = FraudDetectionConfig(high_amount_threshold=Decimal("50000"))
service = FraudDetectionService(custom_config)
```

All existing tests (`test_fraud_detection.py`) continue to work without modification.

## Benefits

1. **Centralization**: All constants now in one place instead of scattered across the module
2. **Type Safety**: Dataclass provides type hints for all fields
3. **Validation**: Comprehensive validation catches configuration errors early
4. **Immutability**: Frozen dataclass prevents accidental modifications
5. **Testability**: Easy to test with custom configs; 50+ tests added
6. **Documentation**: Self-documenting with field descriptions
7. **Flexibility**: Easy to customize behavior for different environments

## Usage Examples

### Default Configuration
```python
from app.services.fraud_detection import FraudDetectionService

service = FraudDetectionService()
result = service.analyze_transaction(txn, history)
```

### Custom Configuration
```python
from app.config.fraud_detection_config import FraudDetectionConfig
from app.services.fraud_detection import FraudDetectionService
from decimal import Decimal

# Create custom config for stricter fraud detection
strict_config = FraudDetectionConfig(
    high_amount_threshold=Decimal("5000"),  # Lower threshold
    velocity_max_transactions=3,            # Stricter velocity
    high_risk_threshold=50,                 # Lower risk threshold
)

service = FraudDetectionService(strict_config)
result = service.analyze_transaction(txn, history)
```

### Testing with Custom Config
```python
def test_custom_rule_behavior():
    config = FraudDetectionConfig(
        high_amount_threshold=Decimal("1000"),
        high_amount_points=100
    )
    rule = HighAmountRule(config)
    # ... test with custom config
```

## Files Summary

| File | Type | Lines | Description |
|------|------|-------|-------------|
| `app/config/__init__.py` | New | 4 | Config package init |
| `app/config/fraud_detection_config.py` | New | 124 | Config dataclass & validation |
| `app/services/fraud_detection.py` | Modified | 195 | Updated to use config |
| `tests/test_fraud_detection_config.py` | New | 321 | Comprehensive config tests |
| **Total** | | **644** | **4 files** |

## Testing

Run config tests:
```bash
pytest tests/test_fraud_detection_config.py -v
```

Run all fraud detection tests:
```bash
pytest tests/test_fraud_detection*.py -v
```

Verify configuration:
```bash
python3 verify_config.py
```

## Configuration Reference

### Rule Thresholds
- `high_amount_threshold`: Decimal = 10000 (USD)
- `velocity_max_transactions`: int = 5
- `velocity_time_window_hours`: int = 1
- `geographic_time_window_hours`: int = 4
- `geographic_distance_threshold_km`: float = 500.0
- `unusual_time_start_hour`: int = 2 (24-hour format)
- `unusual_time_end_hour`: int = 5 (24-hour format)
- `home_country_code`: str = "US"
- `amount_deviation_multiplier`: int = 3
- `amount_deviation_min_transactions`: int = 3

### Risk Thresholds
- `high_risk_threshold`: int = 70 (points)
- `medium_risk_threshold`: int = 40 (points)

### Risk Points
- `high_amount_points`: int = 30
- `velocity_points`: int = 40
- `geographic_anomaly_points`: int = 50
- `unusual_time_points`: int = 20
- `first_international_points`: int = 25
- `amount_deviation_points`: int = 35

## Migration Notes

For developers working on this codebase:

1. **Creating new rules**: Pass config to rule constructor
2. **Customizing thresholds**: Create custom FraudDetectionConfig instance
3. **Testing**: Use custom configs in tests for isolation
4. **Production**: Adjust defaults in FraudDetectionConfig if needed

## Validation Rules

The config enforces these validation rules:
- All thresholds must be positive
- Hours must be valid (0-23 for start, 0-24 for end)
- Start hour must be less than end hour
- Deviation multiplier must be > 1
- Min transactions must be ≥ 1
- High risk threshold must be > medium risk threshold
- All risk points must be non-negative
