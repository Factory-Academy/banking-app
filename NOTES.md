# Feature flag prototype notes

Added a small env-driven feature flag helper at `backend/app/utils/feature_flags.py`.

## Current flag

- `FEATURE_FRAUD_AMOUNT_DEVIATION_RULE`
  - `true/1/yes/on` enables the rule
  - `false/0/no/off` disables the rule
  - unset (or unknown value) falls back to default behavior

Default behavior keeps the amount deviation rule enabled.

## Integration point

`FraudDetectionService` now accepts an optional `FeatureFlags` instance and uses it when building rules:

```python
from app.services.fraud_detection import FraudDetectionService
from app.utils.feature_flags import FeatureFlags

service = FraudDetectionService(feature_flags=FeatureFlags())
```

In production, no code changes are needed, set environment variables before starting the backend.
