# Fraud Detection Service

The `FraudDetectionService` is responsible for evaluating banking transactions for potential fraudulent activity.

## Responsibilities

- **Risk Assessment**: Analyzes incoming transactions against historical account data to calculate a risk score.
- **Rule Evaluation**: Executes a suite of extensible fraud detection rules, including:
    - **High Amount**: Flags transactions exceeding a predefined threshold (e.g., $10,000).
    - **Velocity**: Monitors transaction frequency within a short time window.
    - **Geographic Anomaly**: Detects impossible travel distances between consecutive transactions.
    - **Unusual Timing**: Flags transactions occurring during high-risk time windows (e.g., 2 AM - 5 AM).
    - **Amount Deviation**: Compares transaction amounts against the account's historical average.
- **Decisioning**: Categorizes transactions into risk levels (Low, Medium, High) and determines the initial transaction status (Cleared or Held).

## Implementation Details

The service is located at `backend/app/services/fraud_detection.py` and uses an abstract `FraudRule` class to allow for easy addition of new detection logic.
