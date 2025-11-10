# Transaction Monitoring System - Architecture

## System Overview

The Transaction Monitoring System is a full-stack web application designed to help fraud analysts review high-risk banking transactions. The system automatically analyzes transactions using rule-based fraud detection and flags suspicious ones for manual review.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│                    (http://localhost:5173)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ HTTP/REST
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     Frontend (React)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Components:                                         │  │
│  │  - Layout (Header, Nav, Stats)                      │  │
│  │  - TransactionCard (Display transaction)            │  │
│  │  - ReviewModal (Review form + history)              │  │
│  │                                                       │  │
│  │  Pages:                                              │  │
│  │  - HeldTransactions (Work queue)                    │  │
│  │  - AllTransactions (Full list)                      │  │
│  │  - EscalatedTransactions                            │  │
│  │  - ReviewedTransactions (Audit trail)               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  React Query (State Management + Caching)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ REST API
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   Backend (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes (API Endpoints):                             │  │
│  │  - GET /transactions (List with filters)            │  │
│  │  - GET /transactions/{id} (Single transaction)      │  │
│  │  - GET /transactions/{id}/history (Account history) │  │
│  │  - POST /transactions/{id}/review (Review action)   │  │
│  │  - GET /stats/dashboard (Statistics)                │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Services (Business Logic):                          │  │
│  │  - FraudDetectionService                             │  │
│  │    • 6 Fraud Rules (High Amount, Velocity, etc.)    │  │
│  │    • Risk Score Calculator                           │  │
│  │    • Status Determiner (CLEARED vs HELD)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│                            │                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ORM (SQLAlchemy)                                     │  │
│  │  - Transaction Model                                  │  │
│  │  - Session Management                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ SQL
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Database (SQLite)                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  transactions                                         │  │
│  │  - id (PK)                                            │  │
│  │  - account_number, account_holder_name               │  │
│  │  - amount, merchant_name, transaction_type           │  │
│  │  - location_city, location_country, lat/lng          │  │
│  │  - timestamp                                          │  │
│  │  - status (CLEARED, HELD, APPROVED, REJECTED)        │  │
│  │  - risk_level (LOW, MEDIUM, HIGH)                    │  │
│  │  - risk_score (0-100)                                │  │
│  │  - fraud_flags (JSON array)                          │  │
│  │  - reviewed_by, reviewed_at, review_notes            │  │
│  │                                                       │  │
│  │  Indexes:                                             │  │
│  │  - account_number                                     │  │
│  │  - timestamp                                          │  │
│  │  - status                                             │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web Framework | FastAPI 0.115+ | High-performance async web framework |
| ORM | SQLAlchemy 2.0+ | Database abstraction and models |
| Validation | Pydantic 2.9+ | Request/response validation |
| Database | SQLite | Embedded database (dev), PostgreSQL-ready |
| Testing | pytest, pytest-cov | Unit and integration testing |
| Linting | Ruff | Fast Python linter |
| Type Checking | mypy | Static type checking |
| Security | Bandit | Security vulnerability scanner |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UI Library | React 18 | Component-based UI |
| Language | TypeScript | Type-safe JavaScript |
| Build Tool | Vite 5 | Fast build and dev server |
| Styling | TailwindCSS 3 | Utility-first CSS |
| Routing | React Router 6 | Client-side routing |
| Data Fetching | React Query (TanStack) | Server state management |
| Icons | Lucide React | Icon library |
| Testing | Vitest | Unit testing |
| Linting | ESLint | Code quality |

## Data Flow

### 1. Transaction Creation (via API)

```
Client/Seed Script
    ↓
POST /api/v1/transactions
    ↓
Backend receives TransactionCreate data
    ↓
Generate unique Transaction ID (UUID)
    ↓
Fetch account history from DB
    ↓
Create Transaction object
    ↓
FraudDetectionService.analyze()
    ├─→ HighAmountRule.evaluate()
    ├─→ VelocityRule.evaluate()
    ├─→ GeographicAnomalyRule.evaluate()
    ├─→ UnusualTimeRule.evaluate()
    ├─→ FirstInternationalRule.evaluate()
    └─→ AmountDeviationRule.evaluate()
    ↓
Calculate Total Risk Score
    ↓
Determine Risk Level & Status
    ├─→ Score < 40: LOW, CLEARED
    ├─→ Score 40-69: MEDIUM, CLEARED
    └─→ Score ≥ 70: HIGH, HELD
    ↓
Save to Database
    ↓
Return TransactionResponse (201 Created)
```

**Note:** The seed script (`seed_data.py`) acts as an external data source, sending transactions via the POST API endpoint without any knowledge of the fraud detection rules. This simulates how a real payment processor would integrate with the system. The script will fail with a clear error message if the API is not running.

### 2. Analyst Review Workflow

```
Frontend: User clicks "Review Transaction"
    ↓
API Call: GET /transactions/{id}
    ↓
API Call: GET /transactions/{id}/history
    ↓
ReviewModal displays:
    - Transaction details
    - Fraud flags
    - Account history
    - Stats (avg amount, common locations)
    ↓
Analyst makes decision:
    - APPROVED → Release payment
    - REJECTED → Block permanently
    - ESCALATED → Send to senior analyst
    ↓
API Call: POST /transactions/{id}/review
    {
        "decision": "APPROVED",
        "notes": "Verified with customer",
        "reviewed_by": "Sarah Johnson"
    }
    ↓
Backend updates transaction:
    - status = decision
    - reviewed_at = now()
    - reviewed_by = analyst name
    - review_notes = notes
    ↓
React Query invalidates cache
    ↓
UI updates:
    - Transaction removed from HELD queue
    - Stats updated
    - Appears in Reviewed tab
```

## Fraud Detection Rules

### Rule Evaluation Logic

Each rule implements:
```python
class FraudRule(ABC):
    name: str
    risk_points: int
    
    def evaluate(
        self, 
        transaction: Transaction,
        account_history: List[Transaction]
    ) -> bool:
        """Returns True if rule is triggered"""
```

### Rule Details

| Rule | Points | Trigger Condition | Example |
|------|--------|------------------|---------|
| High Amount | 30 | Amount > $10,000 | $15,000 wire transfer |
| Velocity | 40 | >5 transactions in 1 hour | 8 purchases in 30 minutes |
| Geographic Anomaly | 50 | Different country within 4 hours | NYC → Hong Kong in 2 hours |
| Unusual Time | 20 | Transaction 2-5 AM | Purchase at 3:47 AM |
| First International | 25 | First non-US transaction | First wire to London |
| Amount Deviation | 35 | >3x account average | $9,000 when avg is $200 |

### Risk Scoring

```python
total_score = sum(rule.risk_points for rule in triggered_rules)

if total_score >= 70:
    risk_level = HIGH
    status = HELD  # 🔴 Frozen, requires review
elif total_score >= 40:
    risk_level = MEDIUM
    status = CLEARED  # 🟡 Logged, but processed
else:
    risk_level = LOW
    status = CLEARED  # 🟢 Normal, auto-approved
```

## API Design

### RESTful Endpoints

All endpoints prefixed with `/api/v1`

#### Transactions

**Create Transaction:**
```http
POST /transactions

Request Body:
{
  "account_number": "**** 4521",
  "account_holder_name": "John Smith",
  "amount": "1500.00",
  "merchant_name": "Apple Store",
  ...
}

Response 201 Created:
{
  "id": "TXN-A3F2B9C1",
  "status": "CLEARED",
  "risk_level": "MEDIUM",
  "risk_score": 45,
  "fraud_flags": ["first_international"],
  ...
}
```

**List Transactions:**
```http
GET /transactions?status=HELD&risk_level=HIGH&limit=50&offset=0&account_number=****%204521

Response 200 OK:
{
  "transactions": [...],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

**Supports:**
- Pagination (limit, offset)
- Account search (account_number filter)
- Status and risk level filters
- Date range and amount filters

**Get Single Transaction:**
```http
GET /transactions/TXN-8473

Response 200 OK:
{
  "id": "TXN-8473",
  "amount": "8500.00",
  "status": "HELD",
  "risk_level": "HIGH",
  "fraud_flags": ["geographic_anomaly", "unusual_time"],
  ...
}
```

**Get Account History:**
```http
GET /transactions/TXN-8473/history

Response 200 OK:
{
  "account_number": "**** 4521",
  "account_holder_name": "John Smith",
  "transactions": [...],
  "stats": {
    "average_amount": "245.50",
    "transaction_count": 127,
    "common_locations": ["New York, US", "Boston, US"]
  }
}
```

**Review Transaction:**
```http
POST /transactions/TXN-8473/review

Request Body:
{
  "decision": "REJECTED",
  "notes": "Geographic impossibility confirmed",
  "reviewed_by": "Sarah Johnson"
}

Response 200 OK:
{
  "id": "TXN-8473",
  "status": "REJECTED",
  "reviewed_by": "Sarah Johnson",
  "reviewed_at": "2025-11-10T09:15:00Z"
}
```

#### Statistics

**Dashboard Stats:**
```http
GET /stats/dashboard

Response 200 OK:
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

## Frontend Architecture

### Component Hierarchy

```
App (QueryClientProvider + Router)
├── Layout
│   ├── Header (Logo + Title)
│   ├── Navigation (Tabs)
│   ├── AlertBanner (Held count warning)
│   └── StatsCards (4 stat cards)
└── Pages
    ├── HeldTransactions
    │   ├── TransactionCard (multiple)
    │   └── ReviewModal
    │       ├── Transaction Details
    │       ├── Account History Table
    │       └── Review Form
    ├── AllTransactions
    │   ├── FilterBar
    │   └── TransactionCard (multiple)
    ├── EscalatedTransactions
    │   └── TransactionCard (multiple)
    └── ReviewedTransactions
        └── Review History Table
```

### State Management

**Server State (React Query):**
- Transaction lists (with filters)
- Individual transaction details
- Account history
- Dashboard statistics

**Local State (useState):**
- Filter selections
- Modal open/close
- Form inputs (review notes, decision)

**Auto-refresh:**
- Transactions refresh every 30 seconds
- Stats refresh every 30 seconds
- Manual refresh on mutation success

### Routing

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | → `/held` | Redirect to work queue |
| `/held` | HeldTransactions | HIGH risk transactions |
| `/all` | AllTransactions | All transactions + filters |
| `/escalated` | EscalatedTransactions | Need senior review |
| `/reviewed` | ReviewedTransactions | Audit trail |

## Database Design

### Transaction Table

```sql
CREATE TABLE transactions (
    -- Identity
    id TEXT PRIMARY KEY,
    
    -- Account Info
    account_number TEXT NOT NULL,
    account_holder_name TEXT NOT NULL,
    
    -- Transaction Details
    amount DECIMAL(12, 2) NOT NULL,
    merchant_name TEXT NOT NULL,
    merchant_category TEXT,
    transaction_type TEXT,  -- WIRE, CARD, ATM, ACH
    
    -- Location
    location_city TEXT,
    location_country TEXT,
    latitude FLOAT,
    longitude FLOAT,
    
    -- Timing
    timestamp DATETIME NOT NULL,
    
    -- Risk Assessment
    status TEXT NOT NULL,  -- CLEARED, HELD, APPROVED, REJECTED, ESCALATED
    risk_level TEXT NOT NULL,  -- LOW, MEDIUM, HIGH
    risk_score INTEGER DEFAULT 0,
    fraud_flags JSON,  -- ["geographic_anomaly", "unusual_time"]
    
    -- Review Data
    reviewed_by TEXT,
    reviewed_at DATETIME,
    review_notes TEXT,
    
    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);

-- Indexes for performance
CREATE INDEX idx_account_number ON transactions(account_number);
CREATE INDEX idx_timestamp ON transactions(timestamp);
CREATE INDEX idx_status ON transactions(status);
CREATE INDEX idx_status_risk_timestamp ON transactions(status, risk_level, timestamp);
```

### Why SQLite?

**Pros:**
- ✅ Zero setup (embedded)
- ✅ Perfect for demos
- ✅ Works on Windows/Mac/Linux
- ✅ Single file database
- ✅ ACID compliant

**Cons:**
- ❌ Not suitable for production
- ❌ No concurrent writes
- ❌ No built-in replication

**Production Alternative:** PostgreSQL with same schema.

## Security Considerations

### Current State (Demo)

⚠️ **This is a demo app with no authentication**

### Production Requirements

**Must Add:**
1. **Authentication** - OAuth 2.0, JWT tokens
2. **Authorization** - Role-based access control
   - Analyst: Review transactions
   - Senior Analyst: Review escalated
   - Admin: Manage users, view audit logs
3. **Rate Limiting** - Prevent API abuse
4. **Input Validation** - Already using Pydantic, but add SQL injection protection
5. **HTTPS** - TLS/SSL for all communications
6. **Session Management** - Secure session tokens
7. **Audit Logging** - Track all actions
8. **Data Encryption** - Encrypt sensitive fields (account numbers)
9. **CORS** - Restrict allowed origins
10. **SQL Injection Protection** - Use parameterized queries (already done with SQLAlchemy)

### Security Scanning

**Bandit** is configured to scan for:
- SQL injection vulnerabilities
- Hardcoded passwords
- Use of insecure functions
- Shell injection risks

Run: `bandit -r app`

## Performance Considerations

### Backend Optimizations

1. **Database Indexing**
   - Composite index on (status, risk_level, timestamp) for work queue
   - Index on account_number for history lookups

2. **Connection Pooling**
   - Pool size: 20 connections
   - Max overflow: 40
   - Pre-ping: Enabled (health checks)

3. **Pagination**
   - Default limit: 50 transactions
   - Max limit: 500 (prevents huge queries)

4. **Async Operations**
   - FastAPI uses async/await for I/O operations

### Frontend Optimizations

1. **Code Splitting**
   - Vite automatically splits by route
   - Lazy load pages

2. **Caching**
   - React Query caches all API responses
   - 30-second stale time (auto-refetch)

3. **Memoization**
   - Components use React.memo where appropriate
   - Callbacks wrapped in useCallback

4. **Virtualization**
   - Could add react-virtual for 1000+ transaction lists

## Scalability

### Current Capacity

- **Transactions**: 1,000s (SQLite limit: millions)
- **Concurrent Users**: 10-20 (SQLite single-writer)
- **Response Time**: <100ms for most queries

### Scaling to Production

**Vertical Scaling:**
- PostgreSQL instead of SQLite
- Increase server resources (CPU, RAM)
- Add Redis for caching

**Horizontal Scaling:**
- Load balancer (nginx)
- Multiple backend instances
- Read replicas for PostgreSQL
- Separate analytics database

**Architecture Evolution:**
```
SQLite (Demo)
    ↓
PostgreSQL (Small prod)
    ↓
PostgreSQL + Redis (Medium prod)
    ↓
PostgreSQL + Redis + Message Queue (Large prod)
    ↓
Microservices + Kafka + ML (Enterprise)
```

## Testing Strategy

### Backend Tests

**Unit Tests** (test_fraud_detection.py):
- Each fraud rule independently
- Edge cases (boundaries)
- Score calculation logic

**Integration Tests** (test_api.py):
- API endpoints
- Database operations
- Full workflows (create → review → verify)

**Coverage Target:** >80%

### Frontend Tests

**Component Tests**:
- TransactionCard renders correctly
- ReviewModal form validation
- Button click handlers

**Hook Tests**:
- useTransactions fetches data
- useReviewTransaction mutations work
- Cache invalidation

**Coverage Target:** >70%

### Manual Testing

**Smoke Tests:**
1. Start app → see dashboard
2. View held transactions → see 12-15 items
3. Review one transaction → verify state updates
4. Check reviewed tab → see audit trail

## Monitoring & Observability

### Current State (Demo)

**Logs:**
- Uvicorn access logs
- Python logging module
- Console.log in frontend

### Production Requirements

**Must Add:**
1. **Application Monitoring** - Datadog, New Relic
2. **Error Tracking** - Sentry
3. **Log Aggregation** - ELK stack, Splunk
4. **Metrics** - Prometheus + Grafana
5. **Alerts** - PagerDuty
6. **Tracing** - Jaeger, OpenTelemetry

**Key Metrics to Track:**
- Transaction volume (per hour)
- Held transaction count
- Review time (avg, p95, p99)
- API response times
- Error rates
- Database query performance

## Deployment

### Current Setup (Local Dev)

```
Terminal 1: uvicorn app.main:app --reload
Terminal 2: npm run dev
```

### Production Deployment Options

**Option 1: Docker Compose**
```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://...
  
  frontend:
    build: ./frontend
    ports: ["80:80"]
    depends_on: [backend]
  
  postgres:
    image: postgres:16
```

**Option 2: Cloud Platform**
- Backend: AWS ECS, Google Cloud Run, Azure App Service
- Frontend: Vercel, Netlify, Cloudflare Pages
- Database: AWS RDS, Google Cloud SQL

**Option 3: Kubernetes**
- For enterprise scale
- Auto-scaling
- Rolling updates
- Health checks

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**
   - Train anomaly detection model
   - Replace rule-based system with ML
   - Use scikit-learn or TensorFlow

2. **Real-time Notifications**
   - WebSocket connection
   - Toast notifications for new held transactions
   - Browser push notifications

3. **Advanced Analytics**
   - Charts (transaction volume over time)
   - Fraud trends
   - Analyst performance metrics

4. **Export Functionality**
   - Export to CSV/Excel
   - Generate PDF reports
   - Scheduled email reports

5. **Merchant Management**
   - Merchant blacklist
   - Whitelisted merchants (auto-approve)
   - Merchant risk scoring

6. **User Management**
   - Authentication system
   - Role-based access control
   - Audit trail of all actions

## Glossary

- **HELD**: Transaction frozen, waiting for analyst review
- **CLEARED**: Transaction approved, processed immediately
- **APPROVED**: Analyst reviewed and released transaction
- **REJECTED**: Analyst blocked transaction (fraud confirmed)
- **ESCALATED**: Transaction needs senior analyst review
- **Risk Score**: 0-100 numeric score, sum of triggered rule points
- **Risk Level**: LOW (<40), MEDIUM (40-69), HIGH (≥70)
- **Fraud Flags**: List of triggered rule names
- **Work Queue**: List of HELD transactions awaiting review
- **Account History**: Last 30 transactions for an account

## References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- React Documentation: https://react.dev/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- React Query Documentation: https://tanstack.com/query/
- Fraud Detection Patterns: Industry best practices

---

**Questions?** See [README.md](../README.md) or [demo.md](./demo.md)
