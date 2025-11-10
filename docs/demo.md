# Transaction Monitoring System - Demo Guide

## Introduction

Welcome to the Transaction Monitoring System demo! This application showcases how Factory Droids can assist with various software engineering tasks in a banking context.

This demo features:
- **Real-world banking scenario**: Fraud detection and transaction monitoring
- **Work queue interface**: Analysts review high-risk transactions
- **6 fraud detection rules**: Automated risk scoring
- **Full-stack architecture**: FastAPI backend + React frontend
- **Comprehensive testing**: Unit and integration tests with >80% coverage

## What You'll Learn

This demo lets you test Factory Droid capabilities across:

1. **Codebase Research**: Understanding existing code structure
2. **Feature Development**: Adding new functionality
3. **Test Implementation**: Writing comprehensive test suites  
4. **Code Review Automation**: Setting up CI/CD pipelines
5. **Incident Response**: Debugging production issues

---

## Prerequisites

### Required Software

- **Python 3.10+** (3.14 recommended)
- **Node.js 18+** (20 recommended)
- **Git**

### Installation Verification

**Windows (PowerShell):**
```powershell
python --version
node --version
npm --version
git --version
```

**macOS/Linux:**
```bash
python3 --version
node --version
npm --version
git --version
```

---

## Quick Start (5 Minutes)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd finance-research-app
```

### Step 2: Backend Setup

**Windows:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

**macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

### Step 3: Seed the Database

```bash
python -m app.utils.seed_data
```

Expected output:
```
Starting to seed 1000 transactions...
Creating velocity attack scenario...

✅ Database seeded successfully!
Total transactions: 1008
  - HIGH risk (HELD): 12-15
  - MEDIUM risk: 150-180
  - LOW risk: 800-850
Accounts created: 50
```

### Step 4: Start the Backend

```bash
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 5: Frontend Setup (New Terminal)

**Windows:**
```powershell
cd frontend
npm install
npm run dev
```

**macOS/Linux:**
```bash
cd frontend
npm install
npm run dev
```

You should see:
```
  VITE v5.4.11  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 6: Open the Application

Navigate to **http://localhost:5173** in your browser.

You should see:
- Dashboard with 4 stat cards (Pending Review, Approved Today, etc.)
- Alert banner showing "X HIGH RISK transactions require review"
- Navigation tabs: Held Transactions, All Transactions, Escalated, Reviewed

---

## First Look: Application Tour

### The Analyst Workflow

**Scenario**: You're Sarah Johnson, a fraud analyst at the bank. It's 9 AM and you have transactions waiting for review.

#### 1. Dashboard Overview (5 seconds)

The dashboard shows:
- **Pending Review**: 12-15 HIGH risk transactions frozen and waiting
- **Approved Today**: 0 (it's a fresh day)
- **Blocked Today**: 0
- **Escalated**: 0

#### 2. Held Transactions Tab (DEFAULT VIEW)

This is your **work queue**. Each card shows:

```
Transaction #TXN-8473
⚠️ HIGH RISK    🔶 HELD

$8,500.00
John Smith • **** 4521

Electronics Warehouse Ltd
Electronics

📅 Nov 10, 2025, 3:47 AM    📍 Hong Kong, CN

🚩 Fraud Flags:
  ✓ Geographic Anomaly    ✓ Unusual Time    ✓ High Amount

[Review Transaction]
```

#### 3. Review a Transaction

Click **"Review Transaction"** on any held transaction.

A modal appears with:

**Left Side - Transaction Details:**
- Full transaction info
- Risk score breakdown
- All triggered fraud flags

**Right Side - Account History:**
- Last 30 transactions
- Average transaction amount
- Common locations
- Pattern analysis

**Your Decision Options:**
1. **Approve & Release** - Legitimate transaction, process immediately
2. **Reject & Block** - Confirmed fraud, block permanently  
3. **Escalate** - Need senior analyst review

**Required Fields:**
- Analyst Name (pre-filled: Sarah Johnson)
- Investigation Notes (explain your decision)

**Example Review:**

```
Transaction: $8,500 wire to Hong Kong at 3:47 AM
Account History: Customer normally transacts in NYC, average $200
Previous Transaction: $45 gas station in NYC at 2:15 AM (2 hours before)

Decision: REJECT & BLOCK
Notes: "Geographic impossibility - customer in NYC 2 hours ago, 
cannot physically be in Hong Kong. Likely compromised card."
```

After submitting:
- Transaction status updates to REJECTED
- Disappears from "Held" queue  
- Appears in "Reviewed" tab
- Counter updates: "11 HIGH RISK transactions require review"

#### 4. Work Through the Queue

Continue reviewing until all held transactions are resolved.

**Common Scenarios You'll See:**

**Legitimate High-Value Transaction:**
```
$12,000 to UCLA Tuition Payment
Pattern: Happens every semester
Decision: APPROVE
```

**Velocity Attack:**
```
8 transactions in 40 minutes, $300 each
All to "Online Gaming Store"
Decision: REJECT (card testing fraud)
```

**First International Wire:**
```
$5,000 to London, first international transaction
Account is 5 years old with good history
Decision: ESCALATE (needs verification call)
```

---

## Factory Droid Testing Scenarios

Now that you understand the application, let's test the droid's capabilities!

### ⏱️ Time Estimates
- Scenario 1: 15 minutes
- Scenario 2: 30 minutes
- Scenario 3: 20 minutes
- Scenario 4: 25 minutes
- Scenario 5: 20 minutes
- Scenario 6: 15 minutes

**Total: ~2 hours for all scenarios**

---

## 📖 Scenario 1: Codebase Research (15 min)

**Objective**: Use the droid to understand the codebase without reading files manually.

### Tasks

Ask the droid to answer these questions:

#### Q1: How does the fraud detection system work?
```
Prompt: "Explain how the fraud detection system works in this codebase. 
What rules are implemented and how is the risk score calculated?"
```

**Expected Answer Should Include:**
- 6 fraud detection rules (HighAmountRule, VelocityRule, etc.)
- Each rule has a name and risk points
- Rules are evaluated against transaction + account history
- Total score determines risk level: <40=LOW, 40-69=MEDIUM, ≥70=HIGH
- HIGH risk transactions are auto-HELD for review

#### Q2: What is the database schema?
```
Prompt: "Show me the database schema for transactions. 
What fields are stored and what are the indexes?"
```

**Expected Answer Should Include:**
- Transaction model with all fields
- Status enum: CLEARED, HELD, APPROVED, REJECTED, ESCALATED
- Risk level enum: LOW, MEDIUM, HIGH
- Indexes on account_number, timestamp, status
- JSON field for fraud_flags

#### Q3: Where is the review API endpoint?
```
Prompt: "How does the review workflow work? 
Show me the API endpoint and what happens when an analyst reviews a transaction."
```

**Expected Answer Should Include:**
- POST `/api/v1/transactions/{id}/review`
- Accepts decision (APPROVED/REJECTED/ESCALATED), notes, reviewed_by
- Updates transaction status, reviewed_at timestamp
- Returns updated transaction

#### Q4: What triggers a geographic anomaly flag?
```
Prompt: "Explain the geographic anomaly rule. 
What conditions trigger it and how is distance calculated?"
```

**Expected Answer Should Include:**
- Triggers if different country within 4 hours
- Uses Haversine formula to calculate distance
- Flags if >500km apart
- Uses lat/long coordinates

### Success Criteria
- ✅ Droid reads relevant files (fraud_detection.py, models, routes)
- ✅ Provides accurate explanations
- ✅ Can trace code flow across multiple files
- ✅ Understands business logic

---

## 🛠️ Scenario 2: Add New Feature - Merchant Blacklist (30 min)

**Objective**: Implement a merchant blacklist feature from scratch.

### Requirements

Create a feature where analysts can blacklist merchants. Any transaction from a blacklisted merchant should automatically be flagged as HIGH risk and HELD.

**Components Needed:**
1. New database model: `BlacklistedMerchant`
2. Database migration
3. API endpoints: GET, POST, DELETE for blacklist management
4. New fraud rule: `BlacklistRule`
5. Frontend UI to manage blacklist
6. Tests for new functionality

### Detailed Steps

Ask the droid:

```
Prompt: "Add a merchant blacklist feature to this application.

Requirements:
1. Create a new database table 'blacklisted_merchants' with columns:
   - id (primary key)
   - merchant_name (unique, not null)
   - reason (text)
   - added_by (analyst name)
   - added_at (timestamp)

2. Create API endpoints:
   - GET /api/v1/blacklist - list all blacklisted merchants
   - POST /api/v1/blacklist - add merchant to blacklist
   - DELETE /api/v1/blacklist/{id} - remove from blacklist

3. Add a new fraud detection rule that checks if merchant is blacklisted.
   If blacklisted, automatically set risk level to HIGH and status to HELD.

4. Create a frontend page to manage the blacklist (add/view/remove merchants).

5. Write tests for the new rule and API endpoints.

6. Test with the existing POST /api/v1/transactions endpoint to ensure 
   transactions from blacklisted merchants are automatically flagged.

Please implement this feature end-to-end."
```

### Expected Droid Actions

1. **Create Model** (`backend/app/models/blacklist.py`)
2. **Generate Migration** (Alembic migration file)
3. **Add Routes** (`backend/app/routes/blacklist.py`)
4. **Create BlacklistRule** (in `fraud_detection.py`)
5. **Update Main App** (register new router)
6. **Frontend Component** (`BlacklistManager.tsx`)
7. **Add Route** (in App.tsx)
8. **Write Tests** (`test_blacklist.py`)

### Testing the Feature

After implementation:

1. **Start the app** and go to the new Blacklist page
2. **Add a merchant**: "Suspicious Electronics Ltd"
3. **Trigger the rule**: 
   - Manually create a transaction with that merchant
   - Check it's automatically HELD with HIGH risk
4. **Verify in database**:
   ```bash
   sqlite3 backend/transactions.db
   SELECT * FROM blacklisted_merchants;
   ```

### Success Criteria
- ✅ Database migration runs successfully
- ✅ API endpoints work (test with curl or Postman)
- ✅ BlacklistRule integrates into fraud detection
- ✅ Frontend UI functional (add/remove merchants)
- ✅ Tests pass with >80% coverage
- ✅ Blacklisted merchant transactions are auto-HELD

---

## 🧪 Scenario 3: Implement Test Cases (20 min)

**Objective**: Improve test coverage for critical components.

### Tasks

```
Prompt: "Improve test coverage for the fraud detection module.

Requirements:
1. Write comprehensive unit tests for all 6 fraud detection rules:
   - Test triggering conditions
   - Test edge cases (exactly $10k, 1:59 AM vs 2:00 AM, etc.)
   - Test that rules don't trigger when they shouldn't

2. Test the risk score calculation:
   - Multiple rules triggering together
   - Verify risk level thresholds (LOW, MEDIUM, HIGH)
   - Verify status assignment (CLEARED vs HELD)

3. Add integration tests:
   - Create a transaction → verify fraud detection runs
   - Review a transaction → verify status updates
   - Check that reviewed transactions don't re-enter queue

4. Run tests and achieve >90% coverage for fraud_detection.py

5. Fix any failing tests."
```

### Specific Test Cases to Cover

**Edge Cases:**
```python
# Amount exactly at threshold
test_amount_exactly_10000()  # Should NOT trigger

# Time boundaries
test_transaction_at_159am()  # Should NOT trigger unusual_time
test_transaction_at_200am()  # SHOULD trigger unusual_time
test_transaction_at_459am()  # SHOULD trigger unusual_time
test_transaction_at_500am()  # Should NOT trigger

# Velocity edge case
test_exactly_5_transactions_in_hour()  # Should NOT trigger
test_6_transactions_in_hour()  # SHOULD trigger

# Geographic anomaly
test_same_country_different_city()  # Should NOT trigger
test_different_country_within_4_hours()  # SHOULD trigger
test_different_country_after_5_hours()  # Should NOT trigger
```

### Running Tests

```bash
cd backend
pytest --cov=app --cov-report=term --cov-report=html
```

Expected output:
```
============ test session starts ============
collected 45 items

tests/test_fraud_detection.py .......... [100%]
tests/test_api.py ........ [100%]

----------- coverage: platform darwin, python 3.14.0 -----------
Name                                    Stmts   Miss  Cover
-----------------------------------------------------------
app/services/fraud_detection.py           145      8    94%
app/routes/transactions.py                  89      5    94%
app/models/transaction.py                   35      2    94%
-----------------------------------------------------------
TOTAL                                      523     25    95%

============ 45 passed in 2.5s =============
```

### Success Criteria
- ✅ All edge cases tested
- ✅ >90% coverage for fraud_detection.py
- ✅ All tests pass
- ✅ No false positives/negatives in rule logic

---

## 🤖 Scenario 4: Automated Code Review (25 min)

**Objective**: Set up GitHub Actions to automatically review pull requests.

### Tasks

```
Prompt: "Set up GitHub Actions CI/CD pipeline for this project.

Requirements:

1. Create .github/workflows/ci.yml with separate jobs for backend and frontend:

Backend job should:
- Install Python dependencies
- Run ruff linter (fail on errors)
- Run mypy type checker (fail on errors)
- Run pytest with coverage (fail if <80%)
- Run bandit security scanner

Frontend job should:
- Install npm dependencies
- Run ESLint (fail on errors)  
- Run TypeScript type checker (fail on errors)
- Run tests with coverage (fail if <70%)
- Build the project (fail if build errors)

2. Configure to run on:
- Every pull request to main
- Every push to main

3. Test the workflow:
- Create a test branch
- Make a small change
- Push and create a PR
- Verify all checks pass

Please implement this CI pipeline."
```

### Expected Workflow File

```yaml
name: CI Pipeline

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Lint
        run: cd backend && ruff check .
      - name: Type check
        run: cd backend && mypy app
      - name: Test
        run: cd backend && pytest --cov=app --cov-fail-under=80
      - name: Security scan
        run: cd backend && bandit -r app

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Lint
        run: cd frontend && npm run lint
      - name: Type check
        run: cd frontend && npm run type-check
      - name: Build
        run: cd frontend && npm run build
```

### Testing the Pipeline

1. **Create a test branch**:
   ```bash
   git checkout -b test-ci-pipeline
   ```

2. **Make a small change** (e.g., add a comment in README)

3. **Push and create PR**:
   ```bash
   git add .
   git commit -m "test: verify CI pipeline"
   git push origin test-ci-pipeline
   gh pr create --title "Test CI Pipeline" --body "Testing automated checks"
   ```

4. **Verify checks run** in GitHub PR interface

### Success Criteria
- ✅ Workflow file created and valid
- ✅ All checks pass on current codebase
- ✅ Test PR shows green checkmarks
- ✅ Failed checks block PR merge (configure branch protection)

---

## 🚨 Scenario 5: Incident Response - Database Connection Issue (20 min)

**Objective**: Debug and fix a production issue from logs.

### The Problem

**Setup**: First, create the buggy code:

```
Prompt: "There's a reported issue with database connections timing out under load.
I'm going to give you some error logs. Investigate and fix the issue.

Error logs:
```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached
Connection pool timeout: 30s exceeded
File: app/database.py, line 8
```

Find the root cause and implement a fix."
```

### Investigation Steps (AI Should Do)

1. **Read database.py** - check connection pool configuration
2. **Identify issue**: Pool size too small for production load
3. **Research best practices**: Typical pool sizes for web apps
4. **Propose fix**: Increase pool_size, add pool_pre_ping

### The Fix

**Current (Buggy) Code:**
```python
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    pool_size=5,  # Too small!
    max_overflow=10
)
```

**Fixed Code:**
```python
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    pool_size=20,          # Increased
    max_overflow=40,       # Increased
    pool_pre_ping=True     # Added health check
)
```

### Testing the Fix

**Simulate Load** (optional):
```python
# test_load.py
import concurrent.futures
import requests

def make_request():
    response = requests.get("http://localhost:8000/api/v1/transactions")
    return response.status_code

with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    futures = [executor.submit(make_request) for _ in range(100)]
    results = [f.result() for f in futures]
    
print(f"Success rate: {results.count(200)}/100")
```

Before fix: ~60/100 (timeouts)  
After fix: 100/100 (all succeed)

### Success Criteria
- ✅ Root cause identified (pool too small)
- ✅ Fix implemented (increased pool size + health check)
- ✅ Application handles 100 concurrent requests
- ✅ No more timeout errors in logs

---

## 🐛 Scenario 6: Incident Response - Null Reference Bug (15 min)

**Objective**: Fix a bug causing application crashes.

### The Problem

```
Prompt: "Users are reporting the application crashes when viewing transaction 
history for newly created accounts.

Error logs:
```
TypeError: 'NoneType' object is not iterable
File: app/routes/transactions.py, line 87
Endpoint: GET /api/v1/transactions/{id}/history
```

Debug and fix this issue. Also add a test to prevent regression."
```

### Investigation Steps

1. **Read the error** - NoneType iteration error
2. **Check line 87** in transactions.py
3. **Identify issue**: Missing null check for empty account history
4. **Reproduce bug**: Query transaction for account with no history

### The Bug

**Current (Buggy) Code:**
```python
@router.get("/{transaction_id}/history")
def get_account_history(transaction_id: str, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404)
    
    transactions = db.query(Transaction)\
        .filter(Transaction.account_number == transaction.account_number)\
        .all()
    
    # BUG: transactions could be None or empty!
    amounts = [Decimal(str(t.amount)) for t in transactions]  # Line 87
    avg_amount = sum(amounts) / len(amounts)
    ...
```

**Fixed Code:**
```python
@router.get("/{transaction_id}/history")
def get_account_history(transaction_id: str, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404)
    
    transactions = db.query(Transaction)\
        .filter(Transaction.account_number == transaction.account_number)\
        .all()
    
    # FIX: Handle empty history
    if not transactions:
        return AccountHistoryResponse(
            account_number=transaction.account_number,
            account_holder_name=transaction.account_holder_name,
            transactions=[],
            stats=AccountStats(
                average_amount=Decimal("0"),
                transaction_count=0,
                common_locations=[],
                first_transaction_date=None
            )
        )
    
    amounts = [Decimal(str(t.amount)) for t in transactions]
    avg_amount = sum(amounts) / len(amounts)
    ...
```

### Add Regression Test

```python
def test_account_history_empty(client, db_session):
    """Test that empty account history doesn't crash"""
    # Create transaction with unique account (no history)
    txn = Transaction(
        id="TXN-NEW",
        account_number="**** 9999",  # New account
        ...
    )
    db_session.add(txn)
    db_session.commit()
    
    # This should not crash
    response = client.get(f"/api/v1/transactions/{txn.id}/history")
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["transaction_count"] == 0
    assert len(data["transactions"]) == 0
```

### Success Criteria
- ✅ Bug identified (missing null check)
- ✅ Fix implemented (handle empty history gracefully)
- ✅ Regression test added
- ✅ All tests pass
- ✅ Application no longer crashes on empty history

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --port 8001
```

#### 2. Python Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Ensure venv is activated
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. Database Not Seeded

**Error:**
```
Transactions list is empty
```

**Solution:**
```bash
cd backend
python -m app.utils.seed_data
```

#### 4. Frontend Build Errors

**Error:**
```
Cannot find module '@/types/transaction'
```

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 5. CORS Errors in Browser

**Error:**
```
Access to fetch blocked by CORS policy
```

**Solution:**
- Ensure backend is running on port 8000
- Frontend is running on port 5173
- Check `app/main.py` has CORS middleware configured

---

## Architecture Overview

### Tech Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- SQLite (database)
- Pydantic (data validation)

**Frontend:**
- React 18 (UI library)
- TypeScript (type safety)
- Vite (build tool)
- TailwindCSS (styling)
- React Query (data fetching)

**Testing:**
- pytest (backend)
- vitest (frontend)

### Key Files

**Backend:**
```
app/
├── main.py                 # FastAPI app + CORS setup
├── database.py             # DB connection + session
├── models/transaction.py   # SQLAlchemy model
├── schemas/transaction.py  # Pydantic schemas
├── services/
│   └── fraud_detection.py  # 6 fraud rules + scoring
└── routes/
    ├── transactions.py     # Transaction CRUD + review
    └── stats.py            # Dashboard stats
```

**Frontend:**
```
src/
├── App.tsx                 # Router + QueryClient
├── api/client.ts           # API functions
├── hooks/
│   ├── useTransactions.ts  # React Query hooks
│   └── useStats.ts
├── components/
│   ├── Layout.tsx          # Header + nav + stats cards
│   ├── TransactionCard.tsx # Individual transaction
│   └── ReviewModal.tsx     # Review form + history
└── pages/
    ├── HeldTransactions.tsx    # Work queue
    ├── AllTransactions.tsx     # Full list + filters
    ├── EscalatedTransactions.tsx
    └── ReviewedTransactions.tsx  # Audit trail
```

---

## Next Steps

After completing the demo scenarios:

### Explore Further

1. **Add more fraud rules**:
   - IP address blacklist
   - Device fingerprinting
   - Transaction pattern anomalies

2. **Enhance the UI**:
   - Add charts (transaction volume over time)
   - Map visualization of transaction locations
   - Real-time notifications (WebSocket)

3. **Add authentication**:
   - OAuth login
   - Role-based access control (analyst vs senior analyst)
   - Audit logs

4. **Integrate ML**:
   - Train anomaly detection model
   - Use scikit-learn or TensorFlow
   - Replace rule-based system with ML predictions

5. **Deploy to production**:
   - Containerize with Docker
   - Deploy to AWS/GCP/Azure
   - Set up monitoring (Sentry, Datadog)

### Share Feedback

This demo is designed to showcase Factory Droid capabilities. If you have:
- **Bugs to report**
- **Features to suggest**
- **Questions about the code**

Please open an issue in the repository!

---

## Summary

You've successfully:

✅ Set up a full-stack banking application  
✅ Understood the analyst workflow  
✅ Tested Factory Droid capabilities across 6 scenarios  
✅ Added features, wrote tests, debugged issues  
✅ Experienced real-world software engineering tasks  

**Key Takeaway**: Factory Droids excel at understanding existing codebases, implementing features, writing tests, and debugging issues - making them powerful tools for software engineering teams.

---

**Questions?** Check the [README.md](../README.md) or [architecture.md](./architecture.md) for more details.
