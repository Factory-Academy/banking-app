# Services Module Overview

## Purpose

The `app/services/` module encapsulates the core business logic for transaction analysis and risk assessment. It provides a clean separation between API request handling (routes) and domain-specific fraud detection logic.

## Key Components

### FraudDetectionService

The main service that orchestrates fraud rule evaluation and risk scoring.

**Responsibilities:**
- Evaluates transactions against 6 configurable fraud detection rules
- Calculates cumulative risk scores
- Determines transaction status (CLEARED, HELD) based on risk thresholds
- Returns detailed fraud flags for UI display and audit trails

**Risk Scoring Model:**
- **LOW** (<40 points): Auto-approved, immediately cleared
- **MEDIUM** (40-69 points): Logged for review, cleared automatically
- **HIGH** (≥70 points): Auto-held, requires analyst manual review

### Fraud Rules (Rule Pattern)

Each rule is a separate class inheriting from `FraudRule` (abstract base class):

| Rule | Points | Trigger |
|------|--------|---------|
| HighAmountRule | 30 | Transactions > $10,000 |
| VelocityRule | 40 | >5 transactions in 1 hour |
| GeographicAnomalyRule | 50 | Different country within 4 hours (>500km) |
| UnusualTimeRule | 20 | Transactions 2-5 AM |
| FirstInternationalRule | 25 | First transaction outside US |
| AmountDeviationRule | 35 | Amount >3x account average |

**Rule Pattern Benefits:**
- Easy to add new rules without modifying core logic
- Each rule self-contained and testable
- Rules can be enabled/disabled by modifying the service initialization

## Integration Points

### Called by: Routes

Routes in `app/routes/` invoke the service:

```python
# Example from transaction review route
fraud_service = FraudDetectionService()
analysis = fraud_service.analyze_transaction(transaction, account_history)
```

### Depends on: Models

Consumes ORM models from `app/models/`:
- `Transaction` (the transaction being analyzed)
- `RiskLevel` and `TransactionStatus` enums

### Consumed by: API Responses

Service output is wrapped in Pydantic schemas (`app/schemas/`) for API responses.

## Related Modules

- **routes/transactions.py** - API endpoints that trigger fraud analysis
- **models/transaction.py** - Domain model and status/risk enums
- **schemas/** - Pydantic models for request/response validation
- See [Architecture](architecture.md) for system-wide context
- See [API Docs](api.md) for endpoint specifications

## Design Patterns

- **Strategy Pattern**: Each fraud rule implements a common interface
- **Service Locator**: FraudDetectionService manages rule instances
- **Immutable Configuration**: Rules are initialized once, unchanged during request processing
