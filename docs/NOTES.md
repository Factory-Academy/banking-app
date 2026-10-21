# Module Notes: Fraud Detection Service

## Overview

The **Fraud Detection Service** (`backend/app/services/fraud_detection.py`) is the core business logic module responsible for analyzing banking transactions and identifying potentially fraudulent activity. It implements a rule-based scoring system that automatically determines transaction risk levels and decides whether transactions should be cleared or held for manual review.

## Module Responsibilities

### Primary Functions

1. **Transaction Risk Assessment**: Evaluates incoming transactions against a suite of fraud detection rules
2. **Risk Scoring**: Calculates cumulative risk scores based on triggered rules
3. **Status Determination**: Automatically assigns transaction status (CLEARED or HELD) based on risk thresholds
4. **Flag Management**: Tracks which specific fraud rules were triggered for analyst review

### Architecture Pattern

The module follows the **Strategy Pattern** with a base `FraudRule` abstract class and concrete rule implementations. This design enables:
- Easy addition of new fraud rules without modifying existing code
- Independent testing of individual rules
- Flexible rule composition and scoring adjustments

## Fraud Detection Rules

The service implements **6 fraud detection rules**, each with assigned risk points:

| Rule | Points | Trigger Condition |
|------|--------|-------------------|
| **High Amount** | 30 | Transaction exceeds $10,000 |
| **Velocity** | 40 | More than 5 transactions within 1 hour |
| **Geographic Anomaly** | 50 | Different country within 4 hours (>500km) |
| **Unusual Time** | 20 | Transaction between 2 AM - 5 AM |
| **First International** | 25 | First non-US transaction for account |
| **Amount Deviation** | 35 | Amount >3x account average |

## Risk Level Determination

Risk scores map to levels and statuses as follows:

- **LOW** (<40 points): Auto-approved, status = `CLEARED`
- **MEDIUM** (40-69 points): Logged but cleared, status = `CLEARED`  
- **HIGH** (≥70 points): Held for review, status = `HELD`

## Key Classes

### `FraudRule` (Abstract Base Class)

Defines the interface for all fraud detection rules:
- `name`: Rule identifier
- `risk_points`: Score added when rule triggers
- `evaluate()`: Abstract method implemented by concrete rules

### `FraudDetectionService`

Main service class that orchestrates fraud analysis:
- Maintains collection of all fraud rules
- `analyze_transaction()`: Runs all rules and returns risk assessment dictionary

## Integration Points

- **Called by**: Transaction creation endpoint (`POST /api/v1/transactions`)
- **Requires**: Account transaction history from database
- **Returns**: Dictionary containing `risk_score`, `risk_level`, `status`, and `fraud_flags`
- **Updates**: Transaction model fields automatically based on analysis results

## Usage Example

```python
service = FraudDetectionService()
result = service.analyze_transaction(transaction, account_history)

# Returns:
# {
#     "risk_score": 85,
#     "risk_level": RiskLevel.HIGH,
#     "status": TransactionStatus.HELD,
#     "fraud_flags": ["high_velocity", "geographic_anomaly"]
# }
```

## Notes for Developers

- **Extensibility**: Add new rules by subclassing `FraudRule` and registering in `FraudDetectionService.__init__()`
- **Testing**: Each rule can be tested independently with mock transaction data
- **Performance**: Geographic calculations use Haversine formula for accurate distance computation
- **Tuning**: Risk points and thresholds can be adjusted based on false positive/negative rates

---

**Related Documentation:**
- [API Documentation](api.md) - Transaction creation endpoint
- [Architecture](architecture.md) - Full system design
- [Demo Guide](demo.md) - Scenarios involving fraud detection
