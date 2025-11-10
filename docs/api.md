# API Documentation

Base URL: `http://localhost:8000/api/v1`

## Transactions API

### Create Transaction

**POST** `/transactions`

Create a new transaction and run fraud detection in real-time.

**Request Body:**
```json
{
  "account_number": "**** 4521",
  "account_holder_name": "John Smith",
  "amount": "1500.00",
  "merchant_name": "Apple Store",
  "merchant_category": "Electronics",
  "transaction_type": "CARD",
  "location_city": "New York",
  "location_country": "US",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "timestamp": "2025-11-10T14:30:00Z"
}
```

**Response 201 Created:**
```json
{
  "id": "TXN-A3F2B9C1",
  "account_number": "**** 4521",
  "account_holder_name": "John Smith",
  "amount": "1500.00",
  "merchant_name": "Apple Store",
  "merchant_category": "Electronics",
  "transaction_type": "CARD",
  "location_city": "New York",
  "location_country": "US",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "timestamp": "2025-11-10T14:30:00Z",
  "status": "CLEARED",
  "risk_level": "MEDIUM",
  "risk_score": 45,
  "fraud_flags": ["first_international"],
  "reviewed_by": null,
  "reviewed_at": null,
  "review_notes": null,
  "created_at": "2025-11-10T14:30:01Z",
  "updated_at": null
}
```

**Key Features:**
- Auto-generates unique transaction ID
- Fetches account history for fraud detection context
- Runs all 6 fraud rules immediately
- Returns risk assessment with fraud flags
- HIGH risk transactions (score ≥70) are auto-HELD

---

### List Transactions

**GET** `/transactions`

Get a paginated list of transactions with optional filters.

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by status | `HELD`, `CLEARED`, `APPROVED`, `REJECTED`, `ESCALATED` |
| `risk_level` | string | Filter by risk level | `LOW`, `MEDIUM`, `HIGH` |
| `account_number` | string | Filter by account number | `**** 4521` |
| `merchant_name` | string | Filter by merchant (partial match) | `Apple` |
| `date_from` | datetime | Transactions after this date | `2025-11-01T00:00:00Z` |
| `date_to` | datetime | Transactions before this date | `2025-11-10T23:59:59Z` |
| `min_amount` | decimal | Minimum transaction amount | `100.00` |
| `max_amount` | decimal | Maximum transaction amount | `10000.00` |
| `limit` | integer | Results per page (default: 50, max: 500) | `50` |
| `offset` | integer | Pagination offset (default: 0) | `0` |

**Example Request:**
```
GET /transactions?status=HELD&risk_level=HIGH&limit=20&offset=0
```

**Response 200 OK:**
```json
{
  "transactions": [
    {
      "id": "TXN-8473",
      "account_number": "**** 4521",
      "amount": "8500.00",
      "status": "HELD",
      "risk_level": "HIGH",
      "risk_score": 95,
      "fraud_flags": ["geographic_anomaly", "unusual_time"],
      ...
    }
  ],
  "total": 15,
  "limit": 20,
  "offset": 0
}
```

---

### Get Single Transaction

**GET** `/transactions/{transaction_id}`

Retrieve details for a specific transaction.

**Path Parameters:**
- `transaction_id` (string): The transaction ID (e.g., "TXN-8473")

**Response 200 OK:**
```json
{
  "id": "TXN-8473",
  "account_number": "**** 4521",
  "account_holder_name": "John Smith",
  "amount": "8500.00",
  "merchant_name": "Electronics Warehouse Ltd",
  "merchant_category": "Electronics",
  "transaction_type": "WIRE",
  "location_city": "Hong Kong",
  "location_country": "CN",
  "latitude": 22.3193,
  "longitude": 114.1694,
  "timestamp": "2025-11-10T03:47:00Z",
  "status": "HELD",
  "risk_level": "HIGH",
  "risk_score": 95,
  "fraud_flags": ["geographic_anomaly", "unusual_time", "high_amount"],
  "reviewed_by": null,
  "reviewed_at": null,
  "review_notes": null,
  "created_at": "2025-11-10T03:47:01Z",
  "updated_at": null
}
```

**Response 404 Not Found:**
```json
{
  "detail": "Transaction not found"
}
```

---

### Get Account History

**GET** `/transactions/{transaction_id}/history`

Get transaction history and statistics for the account associated with a transaction.

**Path Parameters:**
- `transaction_id` (string): Any transaction ID for the account

**Response 200 OK:**
```json
{
  "account_number": "**** 4521",
  "account_holder_name": "John Smith",
  "transactions": [
    {
      "id": "TXN-8473",
      "amount": "8500.00",
      "timestamp": "2025-11-10T03:47:00Z",
      ...
    },
    {
      "id": "TXN-8472",
      "amount": "45.00",
      "timestamp": "2025-11-10T02:15:00Z",
      ...
    }
  ],
  "stats": {
    "average_amount": "245.50",
    "transaction_count": 127,
    "common_locations": ["New York, US", "Boston, US", "Chicago, US"],
    "first_transaction_date": "2024-06-15T10:30:00Z"
  }
}
```

**Notes:**
- Returns last 30 transactions for the account
- Statistics include average amount, transaction count, top 3 locations
- Common locations sorted by frequency

---

### Review Transaction

**POST** `/transactions/{transaction_id}/review`

Submit a review decision for a held transaction (analyst workflow).

**Path Parameters:**
- `transaction_id` (string): The transaction ID to review

**Request Body:**
```json
{
  "decision": "REJECTED",
  "notes": "Geographic impossibility - customer in NYC 2 hours ago, cannot be in Hong Kong",
  "reviewed_by": "Sarah Johnson"
}
```

**Fields:**
- `decision` (required): Must be `APPROVED`, `REJECTED`, or `ESCALATED`
- `notes` (required): Investigation notes explaining the decision
- `reviewed_by` (required): Name of the analyst

**Response 200 OK:**
```json
{
  "id": "TXN-8473",
  "status": "REJECTED",
  "reviewed_by": "Sarah Johnson",
  "reviewed_at": "2025-11-10T09:15:00Z",
  "review_notes": "Geographic impossibility - customer in NYC 2 hours ago, cannot be in Hong Kong",
  ...
}
```

**Response 400 Bad Request:**
```json
{
  "detail": "Decision must be APPROVED, REJECTED, or ESCALATED"
}
```

**Response 404 Not Found:**
```json
{
  "detail": "Transaction not found"
}
```

---

## Statistics API

### Get Dashboard Statistics

**GET** `/stats/dashboard`

Retrieve statistics for the fraud analyst dashboard.

**Response 200 OK:**
```json
{
  "held_count": 12,
  "approved_today": 45,
  "rejected_today": 8,
  "escalated_count": 3,
  "avg_review_time_minutes": 8.5,
  "transactions_by_risk": {
    "LOW": 1250,
    "MEDIUM": 85,
    "HIGH": 12
  }
}
```

**Fields:**
- `held_count`: Number of transactions currently HELD (needs review)
- `approved_today`: Transactions approved since midnight
- `rejected_today`: Transactions rejected since midnight
- `escalated_count`: Total escalated transactions
- `avg_review_time_minutes`: Average time from creation to review (today only)
- `transactions_by_risk`: Count of transactions by risk level

---

## Error Responses

### Validation Error (422)

Returned when request body fails validation:

```json
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Internal Server Error (500)

```json
{
  "detail": "Internal server error"
}
```

---

## Data Types

### Transaction Status

- `CLEARED`: Normal transaction, auto-approved
- `HELD`: High-risk transaction, frozen and awaiting review
- `APPROVED`: Analyst approved, released for processing
- `REJECTED`: Analyst rejected, permanently blocked
- `ESCALATED`: Requires senior analyst review

### Risk Level

- `LOW`: Risk score < 40 (auto-cleared)
- `MEDIUM`: Risk score 40-69 (cleared but logged)
- `HIGH`: Risk score ≥ 70 (auto-held for review)

### Transaction Type

- `CARD`: Credit/debit card purchase
- `WIRE`: Wire transfer
- `ATM`: ATM withdrawal
- `ACH`: ACH transfer

---

## Fraud Detection Rules

When creating a transaction via POST, these rules run automatically:

| Rule | Points | Condition |
|------|--------|-----------|
| High Amount | 30 | Amount > $10,000 |
| Velocity | 40 | >5 transactions within 1 hour |
| Geographic Anomaly | 50 | Different country within 4 hours (>500km) |
| Unusual Time | 20 | Transaction between 2-5 AM |
| First International | 25 | First non-US transaction for account |
| Amount Deviation | 35 | Amount >3x account average |

**Risk Score = Sum of triggered rule points**

---

## Rate Limiting

No rate limiting currently implemented (demo application).

For production, recommended limits:
- 100 requests per minute per IP
- 10 POST requests per minute per account

---

## Authentication

No authentication currently required (demo application).

For production, implement:
- JWT-based authentication
- Role-based access control (Analyst, Senior Analyst, Admin)
- API key for programmatic access

---

## CORS

Currently allows requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative dev server)

Configure for production domains in `app/main.py`.

---

## Examples

### Creating a High-Risk Transaction

```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "account_number": "**** 1234",
    "account_holder_name": "Test User",
    "amount": "15000.00",
    "merchant_name": "Crypto Exchange",
    "merchant_category": "Cryptocurrency",
    "transaction_type": "WIRE",
    "location_city": "Hong Kong",
    "location_country": "CN",
    "latitude": 22.3193,
    "longitude": 114.1694,
    "timestamp": "2025-11-10T03:00:00Z"
  }'
```

**Expected Response:**
- `status`: "HELD"
- `risk_level`: "HIGH"
- `fraud_flags`: ["high_amount", "unusual_time", "first_international"]

### Searching by Account Number

```bash
curl "http://localhost:8000/api/v1/transactions?account_number=****%204521&limit=10"
```

### Paginating Through Results

```bash
# Page 1
curl "http://localhost:8000/api/v1/transactions?limit=50&offset=0"

# Page 2
curl "http://localhost:8000/api/v1/transactions?limit=50&offset=50"

# Page 3
curl "http://localhost:8000/api/v1/transactions?limit=50&offset=100"
```

---

For more information, see:
- [Architecture Documentation](architecture.md)
- [Demo Guide](demo.md)
- [README](../README.md)
